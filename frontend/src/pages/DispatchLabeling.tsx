import { useState, useEffect, useRef } from "react";
import { Users, Check, X, ArrowRight, Search, Target, CheckCircle, XCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiService } from "@/services/api";

const DispatchLabeling = () => {
  const [currentTicket, setCurrentTicket] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [prediction, setPrediction] = useState<any>(null);
  const [explanation, setExplanation] = useState<[string, number][] | null>(null);
  const [nearestTicket, setNearestTicket] = useState<{ ref: string; label: string; similarity: number; title?: string; description?: string; service?: string; subcategory?: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [confirmation, setConfirmation] = useState<any>(null);
  const { toast } = useToast();
  
  // Track the current prediction ID to prevent stale LIME explanations
  const currentPredictionIdRef = useRef<number>(0);

  // Available models from API
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  
  // Available teams from API
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>("");
  
  // Track if model needs manual assignment (when inference fails with "not trained yet")
  const [needsManualAssignment, setNeedsManualAssignment] = useState<boolean>(false);
  
  // Track selected team for reassignment
  const [selectedReassignTeam, setSelectedReassignTeam] = useState<string>("");

  // Fetch available models from API
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const instancesResponse = await apiService.getInstances();
        
        if (instancesResponse.success && instancesResponse.data) {
          const instances = instancesResponse.data.instances;
          
          // Fetch info for each instance to get accuracy
          const modelPromises = Object.keys(instances).map(async (instanceId) => {
            const instance = instances[instanceId];
            
            // Only process dispatch models
            if (instance.al_type !== 'dispatch') return null;
            
            // Fetch instance info to get f1_scores
            const infoResponse = await apiService.getInstanceInfo(parseInt(instanceId));
            
            let accuracy = null;
            if (infoResponse.success && infoResponse.data?.f1_scores) {
              const f1Scores = infoResponse.data.f1_scores;
              if (f1Scores.length > 0) {
                accuracy = Math.round(f1Scores[f1Scores.length - 1] * 100 * 10) / 10;
              }
            }
            
            // Capitalize model name
            const capitalizedModelName = instance.model_name
              .split(' ')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');
            
            return {
              id: instanceId,
              name: `${capitalizedModelName} v${instanceId}`,
              accuracy,
              status: "active"
            };
          });
          
          const models = (await Promise.all(modelPromises)).filter(m => m !== null);
          models.sort((a, b) => parseInt(b.id) - parseInt(a.id)); // Sort newest first
          
          setAvailableModels(models);
          
          // Set default to first model
          if (models.length > 0 && !selectedModel) {
            setSelectedModel(models[0].id);
          }
        }
      } catch (error) {
        console.error("Failed to load models:", error);
      }
    };

    const fetchTeams = async () => {
      try {
        // Use instance ID 0 with train data path before instance is created
        const trainDataPath = "data/al_demo_train_data.csv";
        const teamsResponse = await apiService.getTeams(0, trainDataPath);
        if (teamsResponse.success && teamsResponse.data) {
          setAvailableTeams(teamsResponse.data.teams);
        }
      } catch (error) {
        console.error("Failed to load teams:", error);
      }
    };

    fetchModels();
    fetchTeams();
  }, []);



  const handleGetNextTicket = async () => {
    if (!selectedModel) {
      toast({
        title: "No Model Selected",
        description: "Please select an active learning model first",
        variant: "destructive",
      });
      return;
    }
    
    setIsLoading(true);
    try {
      // Call /activelearning/<id>/next endpoint with batch size 1
      const nextResponse = await apiService.getNextInstances(parseInt(selectedModel), 1);
      
      if (!nextResponse.success || !nextResponse.data) {
        throw new Error(nextResponse.error?.detail || "Failed to get next ticket");
      }
      
      const queryIdx = nextResponse.data.query_idx;
      if (!queryIdx || queryIdx.length === 0) {
        toast({
          title: "No More Tickets",
          description: "No more tickets available for labeling",
          variant: "destructive",
        });
        return;
      }
      
      // Call /data/tickets endpoint with the returned index
      const ticketsResponse = await apiService.getTickets(parseInt(selectedModel), [queryIdx[0].toString()]);
      
      if (!ticketsResponse.success || !ticketsResponse.data || ticketsResponse.data.tickets.length === 0) {
        throw new Error("Failed to retrieve ticket data");
      }
      
      const ticketData = ticketsResponse.data.tickets[0];
      
      // Transform ticket data to match expected format
      const ticket = {
        id: ticketData.Ref,
        title: ticketData.Title_anon || "No title available",
        description: ticketData.Description_anon || "No description available",
        service: ticketData['Service->Name'] || "Unknown Service",
        subcategory: ticketData['Service subcategory->Name'] || "Unknown Subcategory"
      };
      
      setCurrentTicket(ticket);
      setPrediction(null);
      setConfirmation(null);
      setSelectedReassignTeam("");
      setExplanation(null);
      setNearestTicket(null);
      
      // Auto-generate team recommendation for the new ticket
      handleGetRecommendation(ticket);
      
      toast({
        title: "New Ticket Retrieved",
        description: `Model provided ticket ${ticket.id} for labeling`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get ticket from model",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetRecommendation = async (ticketData: any) => {
    if (!ticketData || !selectedModel) return;
    
    // Increment prediction ID to invalidate any pending LIME requests
    currentPredictionIdRef.current += 1;
    const thisPredictionId = currentPredictionIdRef.current;
    
    setIsLoading(true);
    setPrediction(null);
    setConfirmation(null);
    setExplanation(null);
    setNearestTicket(null);
    
    try {
      // Prepare inference data from ticket
      const inferenceData = {
        service_subcategory_name: ticketData.subcategory,
        service_name: ticketData.service,
        title_anon: ticketData.title,
        description_anon: ticketData.description,
        // Add other fields if available in ticketData
        team_name: undefined,
        last_team_id_name: undefined,
        public_log_anon: undefined
      };
      
      // Call /activelearning/<id>/infer endpoint
      const inferenceResponse = await apiService.infer(parseInt(selectedModel), inferenceData);
      
      if (!inferenceResponse.success || !inferenceResponse.data) {
        // Check if the error is because the model isn't trained yet
        if (inferenceResponse.error?.detail?.includes("not trained yet")) {
          // Set flag to show manual assignment interface
          setNeedsManualAssignment(true);
          return;
        }
        throw new Error(inferenceResponse.error?.detail || "Failed to get team recommendation");
      }
      
      const currentModel = availableModels.find(m => m.id === selectedModel);
      // Backend returns array of predictions; extract first element
      const predictedTeam = Array.isArray(inferenceResponse.data) ? inferenceResponse.data[0] : inferenceResponse.data.prediction;
      
      // Debug logging
      console.log("Inference response:", inferenceResponse.data);
      console.log("Predicted team:", predictedTeam, "Type:", typeof predictedTeam);
      console.log("Available teams:", availableTeams);
      
      // Ensure availableTeams is not empty
      if (!availableTeams || availableTeams.length === 0) {
        throw new Error("No teams available for matching prediction");
      }
      
      // Find the team that matches the prediction
      let recommendedTeam = availableTeams.find(t => 
        t && typeof t === 'string' && 
        predictedTeam && typeof predictedTeam === 'string' &&
        t.toLowerCase().includes(predictedTeam.toLowerCase())
      );
      
      // If no exact match, use the first team as fallback
      if (!recommendedTeam) {
        recommendedTeam = availableTeams[0];
      }
      
      // Ensure recommendedTeam is valid
      if (!recommendedTeam) {
        throw new Error("Could not determine recommended team");
      }
      
      setPrediction({
        team: { name: recommendedTeam, id: recommendedTeam },
        model: currentModel,
        reasoning: `Model ${currentModel?.name} analyzed ticket content and predicted "${predictedTeam}". Based on ${currentModel?.accuracy}% accuracy from training data.`
      });
      // Fire-and-forget LIME explanation; do not block showing prediction
      (async () => {
        try {
          const explainResponse = await apiService.explainLime(parseInt(selectedModel), {
            ticket_data: inferenceData,
            model_id: 0,
          });
          
          // Only update if this is still the current prediction
          if (thisPredictionId === currentPredictionIdRef.current && explainResponse.success && explainResponse.data && explainResponse.data.length > 0) {
            const item = explainResponse.data[0];
            if (item && Array.isArray(item.top_words)) {
              setExplanation(item.top_words);
            }
          }
        } catch (err) {
          console.error("Explain LIME failed", err);
        }
      })();
      
      // Fire-and-forget nearest ticket lookup; do not block showing prediction
      (async () => {
        try {
          const nearestResponse = await apiService.findNearestTicket(parseInt(selectedModel), {
            query_idx: [ticketData.id],
            model_id: 0,
          });
          
          // Only update if this is still the current prediction
          if (thisPredictionId === currentPredictionIdRef.current && nearestResponse.success && nearestResponse.data) {
            const item = nearestResponse.data;
            // Handle both single object and array responses
            const ref = Array.isArray(item.nearest_ticket_ref) ? item.nearest_ticket_ref[0] : item.nearest_ticket_ref;
            const label = Array.isArray(item.nearest_ticket_label) ? item.nearest_ticket_label[0] : item.nearest_ticket_label;
            const similarity = Array.isArray(item.similarity_score) ? item.similarity_score[0] : item.similarity_score;
            
            if (ref && label !== undefined && similarity !== undefined) {
              // Fetch the full ticket details for the nearest ticket
              try {
                const nearestTicketResponse = await apiService.getTickets(parseInt(selectedModel), [ref.toString()]);
                
                if (nearestTicketResponse.success && nearestTicketResponse.data && nearestTicketResponse.data.tickets.length > 0) {
                  const nearestTicketData = nearestTicketResponse.data.tickets[0];
                  
                  setNearestTicket({
                    ref: ref,
                    label: label,
                    similarity: similarity,
                    title: nearestTicketData.Title_anon || "No title available",
                    description: nearestTicketData.Description_anon || "No description available",
                    service: nearestTicketData['Service->Name'] || "Unknown Service",
                    subcategory: nearestTicketData['Service subcategory->Name'] || "Unknown Subcategory"
                  });
                } else {
                  // Fallback if ticket details cannot be fetched
                  setNearestTicket({
                    ref: ref,
                    label: label,
                    similarity: similarity
                  });
                }
              } catch (ticketErr) {
                console.error("Failed to fetch nearest ticket details", ticketErr);
                // Fallback if ticket details cannot be fetched
                setNearestTicket({
                  ref: ref,
                  label: label,
                  similarity: similarity
                });
              }
            }
          }
        } catch (err) {
          console.error("Find nearest ticket failed", err);
        }
      })();
      
      // Reset manual assignment flag since we got a successful prediction
      setNeedsManualAssignment(false);
      
    } catch (error) {
      // Only show error toast if it's not a "model not trained" error
      if (!error.message?.includes("not trained yet")) {
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to get team recommendation",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const updateModelAccuracy = async (modelId: string) => {
    try {
      const infoResponse = await apiService.getInstanceInfo(parseInt(modelId));
      
      if (infoResponse.success && infoResponse.data?.f1_scores) {
        const f1Scores = infoResponse.data.f1_scores;
        if (f1Scores.length > 0) {
          const accuracy = Math.round(f1Scores[f1Scores.length - 1] * 100 * 10) / 10;
          
          // Update the accuracy in availableModels
          setAvailableModels(prevModels => 
            prevModels.map(model => 
              model.id === modelId 
                ? { ...model, accuracy }
                : model
            )
          );
          
          return accuracy;
        }
      }
    } catch (error) {
      console.error("Failed to fetch updated accuracy:", error);
    }
    return null;
  };

  const handleManualTeamAssignment = async () => {
    if (!selectedTeam || !currentTicket || !selectedModel) {
      toast({
        title: "Missing Information",
        description: "Please select a team before confirming",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      // Call /activelearning/<id>/label endpoint
      const labelResponse = await apiService.labelInstance(parseInt(selectedModel), {
        query_idx: [currentTicket.id],
        labels: [selectedTeam]
      });

      if (!labelResponse.success) {
        throw new Error(labelResponse.error?.detail || "Failed to label ticket");
      }

      // Show success confirmation
      const confirmationData = {
        type: "manual",
        message: "Team assigned successfully",
        team: selectedTeam,
        action: `The ticket has been assigned to ${selectedTeam}. This will help train the model for future predictions.`
      };

      setConfirmation(confirmationData);
      
      toast({
        title: "Success!",
        description: `Ticket assigned to ${selectedTeam}`,
      });

      // Reset selection and manual assignment flag
      setSelectedTeam("");
      setNeedsManualAssignment(false);
      
      // Fetch updated accuracy after labeling
      await updateModelAccuracy(selectedModel);
      
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to assign team",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLabelAction = async (action: string, teamId?: string) => {
    if (!currentTicket || !selectedModel) return;
    
    setIsLoading(true);
    let confirmationData;
    let labelToSend = prediction.team.name; // Default to predicted team
    
    try {
      if (action === "correct") {
        confirmationData = {
          type: "correct",
          message: "Assignment confirmed as correct",
          team: prediction.team.name,
          action: "The model's recommendation has been validated and the ticket will be dispatched to the correct team."
        };
      } else if (action === "reassign") {
        const newTeam = availableTeams.find(t => t === teamId);
        labelToSend = newTeam || prediction.team.name;
        confirmationData = {
          type: "reassign",
          message: "Ticket reassigned successfully",
          team: newTeam || "Unknown Team",
          originalTeam: prediction.team.name,
          action: `The ticket has been reassigned from ${prediction.team.name} to ${newTeam}. This feedback will help improve the model's future predictions.`
        };
      } else {
        throw new Error("Invalid action");
      }
      
      // Call /activelearning/<id>/label endpoint
      const labelResponse = await apiService.labelInstance(parseInt(selectedModel), {
        query_idx: [currentTicket.id],
        labels: [labelToSend]
      });

      if (!labelResponse.success) {
        throw new Error(labelResponse.error?.detail || "Failed to label ticket");
      }
      
      setConfirmation(confirmationData);
      
      toast({
        title: confirmationData.message,
        description: confirmationData.action,
      });
      
      // Fetch updated accuracy after labeling
      await updateModelAccuracy(selectedModel);
      
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to process label action",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8 ml-fade-in">
          <h1 className="text-4xl font-bold mb-4">
            <span className="ml-hero-text">Dispatch Labeling Interface</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Review tickets and confirm team assignments for dispatch training
          </p>
        </div>

        {/* Model Selection & Ticket Selection */}
        <Card className="ml-card mb-8 ml-fade-in">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-6 h-6 text-primary" />
              <span>Model & Ticket Selection</span>
            </CardTitle>
            <CardDescription>
              Choose your active learning model and ticket for team assignment review
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="model-select">Active Learning Model</Label>
              <Select value={selectedModel} onValueChange={setSelectedModel} disabled={availableModels.length === 0}>
                <SelectTrigger>
                  <SelectValue placeholder={availableModels.length === 0 ? "No models available" : "-- Select a Model --"} />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center justify-between w-full min-w-0">
                        <div className="flex items-center space-x-2">
                          <span>{model.name}</span>
                          <Badge 
                            variant={model.status === 'active' ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {model.status}
                          </Badge>
                        </div>
                        {model.accuracy !== null && (
                          <span className="text-sm text-muted-foreground ml-2">
                            {model.accuracy}% acc
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedModel && (
                <p className="text-sm text-muted-foreground">
                  Using: {availableModels.find(m => m.id === selectedModel)?.name} 
                  {availableModels.find(m => m.id === selectedModel)?.accuracy !== null && (
                    <span className="text-ml-success ml-2">
                      ({availableModels.find(m => m.id === selectedModel)?.accuracy}% accuracy)
                    </span>
                  )}
                </p>
              )}
            </div>

            {/* Ticket Selection */}
            <div className="space-y-2">
              <Label htmlFor="ticket-retrieve">Current Ticket for Team Assignment</Label>
              {!currentTicket ? (
                <div className="p-4 border-2 border-dashed border-muted-foreground/25 rounded-lg text-center">
                  <p className="text-muted-foreground">No ticket assigned yet</p>
                  <p className="text-sm text-muted-foreground">Click "Get Next Ticket" to retrieve a ticket from the model</p>
                </div>
              ) : (
                <div className="mt-6 space-y-4 ml-scale-in">
                  {/* Ticket Details */}
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold">Model-Provided Ticket</h3>
                      <div className="flex space-x-2">
                        <Badge variant="secondary">{currentTicket.service}</Badge>
                        <Badge variant="outline">{currentTicket.subcategory}</Badge>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <strong>Title:</strong> {currentTicket.title}
                      </div>
                      <div>
                        <strong>Description:</strong>
                        <Textarea
                          value={currentTicket.description}
                          readOnly
                          className="mt-1 min-h-[120px] resize-none"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 flex space-x-3">
              <Button 
                onClick={handleGetNextTicket}
                disabled={!selectedModel || isLoading}
                className="ml-button-primary"
              >
                {isLoading ? (
                  <>
                    <div className="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                    Getting ticket from {availableModels.find(m => m.id === selectedModel)?.name}...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Get Next Ticket
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Confirmation Message */}
        {confirmation && (
          <Card className={`ml-card mb-8 ml-scale-in ${
            confirmation.type === 'correct' ? 'border-ml-success' : 
            confirmation.type === 'reassign' ? 'border-ml-warning' : 
            confirmation.type === 'manual' ? 'border-ml-primary' : 'border-ml-error'
          }`}>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                  confirmation.type === 'correct' ? 'bg-ml-success/10' : 
                  confirmation.type === 'reassign' ? 'bg-ml-warning/10' : 
                  confirmation.type === 'manual' ? 'bg-ml-primary/10' : 'bg-ml-error/10'
                }`}>
                  <CheckCircle className={`w-8 h-8 ${
                    confirmation.type === 'correct' ? 'text-ml-success' : 
                    confirmation.type === 'reassign' ? 'text-ml-warning' : 
                    confirmation.type === 'manual' ? 'text-ml-primary' : 'text-ml-error'
                  }`} />
                </div>
                <h3 className="text-xl font-semibold mb-2">{confirmation.message}</h3>
                {confirmation.type === 'reassign' && (
                  <p className="text-lg mb-2">
                    <span className="line-through text-muted-foreground">{confirmation.originalTeam}</span> 
                    <ArrowRight className="w-4 h-4 inline mx-2" />
                    <span className="font-semibold text-ml-warning">{confirmation.team}</span>
                  </p>
                )}
                {(confirmation.type === 'correct' || confirmation.type === 'manual') && (
                  <p className="text-lg mb-2 font-semibold text-ml-success">{confirmation.team}</p>
                )}
                <p className="text-muted-foreground">{confirmation.action}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Manual Labeling Interface - shown when model not trained yet */}
        {currentTicket && !prediction && !confirmation && needsManualAssignment && (
          <Card className="ml-card mb-8 ml-scale-in">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="w-6 h-6 text-ml-warning" />
                <span>Manual Team Assignment</span>
              </CardTitle>
              <CardDescription>
                Model not trained yet. Please assign the team manually to start training.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
                <h3 className="text-xl font-semibold mb-2">Assign Team</h3>
                <p className="text-muted-foreground mb-4">
                  Select the appropriate team for this ticket to start training the model.
                </p>
                <div className="space-y-4">
                  <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                    <SelectTrigger className="w-64 mx-auto">
                      <SelectValue placeholder="Select team..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableTeams.map((team) => (
                        <SelectItem key={team} value={team}>
                          {team}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button 
                    onClick={handleManualTeamAssignment}
                    disabled={!selectedTeam || isLoading}
                    className="ml-button-primary"
                  >
                    {isLoading ? (
                      <>
                        <div className="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                        Assigning...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Confirm Assignment
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Team Recommendation */}
        {prediction && !confirmation && (
          <Card className="ml-card mb-8 ml-scale-in">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <ArrowRight className="w-6 h-6 text-ml-success" />
                <span>Recommended Team Assignment</span>
              </CardTitle>
              <CardDescription>
                Model prediction for team dispatch
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Team Recommendation */}
              <div className="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
                {isLoading ? (
                  <div className="space-y-3">
                    <div className="ml-pulse w-8 h-8 mx-auto bg-primary rounded-full" />
                    <p className="text-muted-foreground">Analyzing ticket content...</p>
                  </div>
                ) : (
                  <>
                    <h3 className="text-2xl font-bold mb-2">{prediction.team.name}</h3>
                    <p className="text-muted-foreground mb-3">Recommended team assignment</p>
                  </>
                )}
              </div>

              {!isLoading && (
                <>
                  {/* Model Info */}
                  <div className="text-center text-sm text-muted-foreground mb-4">
                    Prediction by: <span className="font-semibold">{prediction.model?.name}</span>
                    {prediction.model?.accuracy !== null && (
                      <Badge variant="outline" className="ml-2">
                        {prediction.model?.accuracy}% accuracy
                      </Badge>
                    )}
                  </div>
                  
                  {/* Reasoning appears after explanation arrives */}
                  {(explanation || nearestTicket) && (
                    <div className="space-y-4">
                      {explanation && (
                        <div className="p-4 bg-muted/30 rounded-lg">
                          <h4 className="font-semibold mb-2">LIME Explanation</h4>
                          <p className="text-sm text-muted-foreground mb-2">{prediction.reasoning}</p>
                          <div className="flex flex-wrap gap-2">
                            {explanation.slice(0, 10).map(([word, weight], idx) => (
                              <span 
                                key={`${word}-${idx}`} 
                                className={`inline-flex items-center rounded border px-2 py-1 text-xs ${
                                  weight > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                                }`}
                              >
                                <span className="mr-1">{word}</span>
                                <Badge 
                                  variant="secondary" 
                                  className={weight > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
                                >
                                  {weight.toFixed(3)}
                                </Badge>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {nearestTicket && (
                        <div className="p-4 bg-muted/30 rounded-lg">
                          <h4 className="font-semibold mb-2">Similar Ticket</h4>
                          <p className="text-sm text-muted-foreground mb-3">
                            Found a previously labeled ticket that is {(nearestTicket.similarity * 100).toFixed(1)}% similar to this one.
                          </p>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Ticket Reference:</span>
                              <Badge variant="outline">{nearestTicket.ref}</Badge>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Assigned Team:</span>
                              <Badge variant="secondary">{nearestTicket.label}</Badge>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Similarity Score:</span>
                              <Badge 
                                variant="outline"
                                className={nearestTicket.similarity > 0.8 ? 'bg-green-50 border-green-200 text-green-700' : 'bg-blue-50 border-blue-200 text-blue-700'}
                              >
                                {(nearestTicket.similarity * 100).toFixed(1)}%
                              </Badge>
                            </div>
                            {nearestTicket.title && (
                              <>
                                <div className="pt-2 border-t">
                                  <div className="flex items-start space-x-2 mb-2">
                                    <Badge variant="secondary">{nearestTicket.service}</Badge>
                                    <Badge variant="outline">{nearestTicket.subcategory}</Badge>
                                  </div>
                                  <div className="space-y-2">
                                    <div>
                                      <span className="text-xs font-medium text-muted-foreground">Title:</span>
                                      <p className="text-sm mt-1">{nearestTicket.title}</p>
                                    </div>
                                    <div>
                                      <span className="text-xs font-medium text-muted-foreground">Description:</span>
                                      <Textarea
                                        value={nearestTicket.description}
                                        readOnly
                                        className="mt-1 min-h-[80px] resize-none text-sm"
                                      />
                                    </div>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3 justify-center pt-4">
                    <div className="flex gap-2 items-center">
                      <Select value={selectedReassignTeam} onValueChange={setSelectedReassignTeam}>
                        <SelectTrigger className="w-48">
                          <SelectValue placeholder="Reassign to..." />
                        </SelectTrigger>
                        <SelectContent>
                          {availableTeams.filter(t => t !== prediction.team.name).map((team) => (
                            <SelectItem key={team} value={team}>
                              {team}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {selectedReassignTeam && (
                        <Button 
                          onClick={() => setSelectedReassignTeam("")}
                          variant="ghost"
                          size="icon"
                          title="Clear selection"
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    
                    <Button 
                      onClick={() => selectedReassignTeam ? handleLabelAction("reassign", selectedReassignTeam) : handleLabelAction("correct")}
                      className={selectedReassignTeam ? "bg-ml-warning hover:bg-ml-warning/90 text-white" : "ml-button-primary"}
                    >
                      {selectedReassignTeam ? (
                        <>
                          <ArrowRight className="w-4 h-4 mr-2" />
                          Reassign to {selectedReassignTeam}
                        </>
                      ) : (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          Correct Assignment
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Teams Overview */}
        <Card className="ml-card ml-fade-in">
          <CardHeader>
            <CardTitle>Available Teams</CardTitle>
            <CardDescription>Overview of teams that can be assigned tickets</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {availableTeams.map((team) => (
                <div key={team} className="p-4 bg-muted/30 rounded-lg">
                  <h4 className="font-semibold mb-1">{team}</h4>
                  <p className="text-sm text-muted-foreground">Available team for ticket assignment</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DispatchLabeling;