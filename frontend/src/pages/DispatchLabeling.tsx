import { useState, useEffect } from "react";
import { Users, Check, X, ArrowRight, Search, Target, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

const DispatchLabeling = () => {
  const [currentTicket, setCurrentTicket] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [prediction, setPrediction] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [confirmation, setConfirmation] = useState<any>(null);
  const { toast } = useToast();

  // Mock available models (newest first)
  const availableModels = [
    { 
      id: "al_1737123456789", 
      name: "Dispatch Model v3.2", 
      created: "2024-01-15T10:30:00Z",
      accuracy: 94.5,
      status: "active"
    },
    { 
      id: "al_1737123456788", 
      name: "Dispatch Model v3.1", 
      created: "2024-01-10T14:20:00Z",
      accuracy: 91.2,
      status: "active"
    },
    { 
      id: "al_1737123456787", 
      name: "Dispatch Model v3.0", 
      created: "2024-01-05T09:15:00Z",
      accuracy: 89.8,
      status: "deprecated"
    }
  ];

  // Set default model to the latest (first in array)
  useEffect(() => {
    if (availableModels.length > 0 && !selectedModel) {
      setSelectedModel(availableModels[0].id);
    }
  }, []);

  const sampleTicketsFromModel = [
    {
      id: "ticket1",
      title: "I need a Jira license to access the project Agile Transformation and track my development tasks",
      description: "Hello, I would like to request a Jira license in order to access the Agile Transformation project. I need to track my assigned development tasks, update their status, and collaborate effectively with my team.",
      service: "IT Support",
      subcategory: "Access Management",
      priority: "Medium",
      uncertainty: 0.89
    },
    {
      id: "ticket2", 
      title: "Laptop screen flickering and going black intermittently",
      description: "My laptop screen has been flickering for the past two days and sometimes goes completely black. I have to restart to get it working again. This is affecting my productivity.",
      service: "IT Support",
      subcategory: "Hardware Issues",
      priority: "High",
      uncertainty: 0.76
    },
    {
      id: "ticket3",
      title: "Request for additional office supplies - printer paper and toner",
      description: "Our department is running low on printer paper and we need a new toner cartridge for the HP LaserJet in the main office. Please arrange for delivery.",
      service: "Facilities",
      subcategory: "Office Supplies",
      priority: "Low",
      uncertainty: 0.93
    }
  ];

  const teams = [
    { id: "it-support", name: "IT Support Team", description: "Hardware, software, and access issues" },
    { id: "facilities", name: "Facilities Team", description: "Office supplies, maintenance, security" },
    { id: "hr", name: "HR Team", description: "Benefits, policies, training" },
    { id: "finance", name: "Finance Team", description: "Expenses, invoicing, budget" }
  ];

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
      const currentModel = availableModels.find(m => m.id === selectedModel);
      // Simulate API call to get ticket from model (highest uncertainty first)
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Select highest uncertainty ticket from available ones
      const ticketFromModel = sampleTicketsFromModel.reduce((prev, current) => 
        (prev.uncertainty > current.uncertainty) ? prev : current
      );
      
      setCurrentTicket(ticketFromModel);
      setPrediction(null);
      setConfirmation(null);
      
      // Auto-generate team recommendation for the new ticket
      handleGetRecommendation(ticketFromModel);
      
      toast({
        title: "New Ticket Retrieved",
        description: `Model provided ticket with ${(ticketFromModel.uncertainty * 100).toFixed(1)}% uncertainty`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get ticket from model",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetRecommendation = async (ticketData: any) => {
    if (!ticketData || !selectedModel) return;
    
    setIsLoading(true);
    setPrediction(null);
    setConfirmation(null);
    
    try {
      // Simulate API call with model-specific logic
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const currentModel = availableModels.find(m => m.id === selectedModel);
      let recommendedTeam = teams[0]; // Default
      
      if (ticketData.service === "IT Support") {
        recommendedTeam = teams.find(t => t.id === "it-support")!;
      } else if (ticketData.service === "Facilities") {
        recommendedTeam = teams.find(t => t.id === "facilities")!;
      }
      
      setPrediction({
        team: recommendedTeam,
        confidence: currentModel ? currentModel.accuracy / 100 : 0.92,
        model: currentModel,
        reasoning: `Model ${currentModel?.name} analyzed ticket content: keywords '${ticketData.service}', '${ticketData.subcategory}' strongly indicate ${recommendedTeam.name} assignment. Based on ${currentModel?.accuracy}% accuracy from training data.`
      });
      
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get team recommendation",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLabelAction = (action: string, teamId?: string) => {
    let confirmationData;
    
    if (action === "correct") {
      confirmationData = {
        type: "correct",
        message: "Assignment confirmed as correct",
        team: prediction.team.name,
        action: "The model's recommendation has been validated and the ticket will be dispatched to the correct team."
      };
    } else if (action === "reassign") {
      const newTeam = teams.find(t => t.id === teamId);
      confirmationData = {
        type: "reassign",
        message: "Ticket reassigned successfully",
        team: newTeam?.name || "Unknown Team",
        originalTeam: prediction.team.name,
        action: `The ticket has been reassigned from ${prediction.team.name} to ${newTeam?.name}. This feedback will help improve the model's future predictions.`
      };
    } else {
      confirmationData = {
        type: "reject",
        message: "Assignment rejected",
        team: prediction.team.name,
        action: "This assignment has been rejected. The ticket will be reviewed manually and this feedback will improve the model."
      };
    }
    
    setConfirmation(confirmationData);
    
    toast({
      title: confirmationData.message,
      description: confirmationData.action,
    });
    
    // Auto-reset after 5 seconds
    setTimeout(() => {
      setCurrentTicket(null);
      setPrediction(null);
      setConfirmation(null);
    }, 5000);
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
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="-- Select a Model --" />
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
                        <span className="text-sm text-muted-foreground ml-2">
                          {model.accuracy}% acc
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedModel && (
                <p className="text-sm text-muted-foreground">
                  Using: {availableModels.find(m => m.id === selectedModel)?.name} 
                  <span className="text-ml-success ml-2">
                    ({availableModels.find(m => m.id === selectedModel)?.accuracy}% accuracy)
                  </span>
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
                        <Badge 
                          variant={currentTicket.priority === 'High' ? 'destructive' : 
                                  currentTicket.priority === 'Medium' ? 'default' : 'secondary'}
                        >
                          {currentTicket.priority}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {(currentTicket.uncertainty * 100).toFixed(1)}% uncertainty
                        </Badge>
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
                          className="mt-1 min-h-[80px] resize-none"
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
            confirmation.type === 'reassign' ? 'border-ml-warning' : 'border-ml-error'
          }`}>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                  confirmation.type === 'correct' ? 'bg-ml-success/10' : 
                  confirmation.type === 'reassign' ? 'bg-ml-warning/10' : 'bg-ml-error/10'
                }`}>
                  <CheckCircle className={`w-8 h-8 ${
                    confirmation.type === 'correct' ? 'text-ml-success' : 
                    confirmation.type === 'reassign' ? 'text-ml-warning' : 'text-ml-error'
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
                {confirmation.type === 'correct' && (
                  <p className="text-lg mb-2 font-semibold text-ml-success">{confirmation.team}</p>
                )}
                <p className="text-muted-foreground">{confirmation.action}</p>
                <p className="text-sm text-muted-foreground mt-3">
                  This page will reset automatically in a few seconds...
                </p>
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
                    <p className="text-muted-foreground mb-3">{prediction.team.description}</p>
                    <Badge variant="default" className="text-lg px-3 py-1">
                      {(prediction.confidence * 100).toFixed(1)}% Confidence
                    </Badge>
                  </>
                )}
              </div>

              {!isLoading && (
                <>
                  {/* Model Info */}
                  <div className="text-center text-sm text-muted-foreground mb-4">
                    Prediction by: <span className="font-semibold">{prediction.model?.name}</span>
                    <Badge variant="outline" className="ml-2">
                      {prediction.model?.accuracy}% accuracy
                    </Badge>
                  </div>
                  
                  {/* Reasoning */}
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <h4 className="font-semibold mb-2">Reasoning</h4>
                    <p className="text-sm text-muted-foreground">{prediction.reasoning}</p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3 justify-center pt-4">
                    <Button 
                      onClick={() => handleLabelAction("correct")}
                      className="ml-button-primary"
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Correct Assignment
                    </Button>
                    
                    <Select onValueChange={(teamId) => handleLabelAction("reassign", teamId)}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="Reassign to..." />
                      </SelectTrigger>
                      <SelectContent>
                        {teams.filter(t => t.id !== prediction.team.id).map((team) => (
                          <SelectItem key={team.id} value={team.id}>
                            {team.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Button 
                      onClick={() => handleLabelAction("reject")}
                      variant="destructive"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Reject
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
              {teams.map((team) => (
                <div key={team.id} className="p-4 bg-muted/30 rounded-lg">
                  <h4 className="font-semibold mb-1">{team.name}</h4>
                  <p className="text-sm text-muted-foreground">{team.description}</p>
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