import { useState, useEffect } from "react";
import { MessageSquare, Check, X, Edit3, Search, Lightbulb } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

const ResolutionLabeling = () => {
  const [currentTicket, setCurrentTicket] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [showKnowledgeBase, setShowKnowledgeBase] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState("");
  const { toast } = useToast();

  // Mock available models (newest first)
  const availableModels = [
    { 
      id: "al_1737123456790", 
      name: "Resolution Model v2.1", 
      created: "2024-01-15T11:30:00Z",
      accuracy: 92.8,
      status: "active"
    },
    { 
      id: "al_1737123456791", 
      name: "Resolution Model v2.0", 
      created: "2024-01-08T16:45:00Z",
      accuracy: 89.5,
      status: "active"
    },
    { 
      id: "al_1737123456792", 
      name: "Resolution Model v1.9", 
      created: "2024-01-01T12:00:00Z",
      accuracy: 85.2,
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
      category: "Access Request",
      priority: "Medium",
      uncertainty: 0.85
    },
    {
      id: "ticket2", 
      title: "Requesting a Jira license to collaborate with my team on the Customer Onboarding project",
      category: "License Request",
      priority: "High",
      uncertainty: 0.92
    },
    {
      id: "ticket3",
      title: "Need Jira access for Digital Banking initiative project management",
      category: "Access Request", 
      priority: "Low",
      uncertainty: 0.78
    }
  ];

  const knowledgeBaseData = [
    {
      description: "Jira license request for project access",
      publicLog: "User requesting project-specific Jira access for development tasks"
    },
    {
      description: "Team collaboration tools access",
      publicLog: "Request for collaborative project management tool access"
    }
  ];

  const defaultResponse = `Dear user,
your Jira license has been successfully assigned.
You can verify your assigned licenses at the following portal: [license portal link].

Please note:

The license grants access to Jira as an application.

To work on a specific project or space, additional permissions may be required.

These project/space-level permissions are managed directly by the respective project administrators.

If you encounter any issues with access or functionality, please reopen the ticket or contact your project manager/project administrator.

Best regards,
Service Desk`;

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
      // Simulate API call to get ticket from model
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Select highest uncertainty ticket from available ones
      const ticketFromModel = sampleTicketsFromModel.reduce((prev, current) => 
        (prev.uncertainty > current.uncertainty) ? prev : current
      );
      
      setCurrentTicket(ticketFromModel);
      setShowKnowledgeBase(false);
      setResponse("");
      
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

  const handleLabelAction = (action: string) => {
    toast({
      title: `Response ${action}`,
      description: `The response has been ${action.toLowerCase()}ed successfully.`,
    });
    
    // Reset current ticket and form
    setCurrentTicket(null);
    setShowKnowledgeBase(false);
    setResponse("");
  };

  const handleScanKnowledgeBase = async () => {
    if (!currentTicket) {
      toast({
        title: "No Ticket Available",
        description: "Please get a ticket from the model first",
        variant: "destructive",
      });
      return;
    }
    
    setIsLoading(true);
    try {
      const currentModel = availableModels.find(m => m.id === selectedModel);
      // Simulate API call with model-specific processing
      await new Promise(resolve => setTimeout(resolve, 1500));
      setShowKnowledgeBase(true);
      
      const enhancedResponse = `${defaultResponse}

--- Model Information ---
Generated by: ${currentModel?.name}
Model Accuracy: ${currentModel?.accuracy}%
Confidence: ${(Math.random() * 0.2 + 0.8).toFixed(2)}`;
      
      setResponse(enhancedResponse);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to scan knowledge base",
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
            <span className="ml-hero-text">Resolution Labeling Interface</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Review tickets and label appropriate responses for resolution training
          </p>
        </div>

        {/* Model Selection & Ticket Selection */}
        <Card className="ml-card mb-8 ml-fade-in">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="w-6 h-6 text-primary" />
              <span>Model & Ticket Selection</span>
            </CardTitle>
            <CardDescription>
              Choose your active learning model and ticket for response labeling
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
              <Label htmlFor="ticket-retrieve">Current Ticket for Labeling</Label>
              {!currentTicket ? (
                <div className="p-4 border-2 border-dashed border-muted-foreground/25 rounded-lg text-center">
                  <p className="text-muted-foreground">No ticket assigned yet</p>
                  <p className="text-sm text-muted-foreground">Click "Get Next Ticket" to retrieve a ticket from the model</p>
                </div>
              ) : (
                <div className="mt-6 p-4 bg-muted/30 rounded-lg ml-scale-in">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold">Model-Provided Ticket</h3>
                    <div className="flex space-x-2">
                      <Badge variant="secondary">{currentTicket.category}</Badge>
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
                  <Textarea
                    value={currentTicket.title}
                    readOnly
                    className="min-h-[100px] resize-none"
                  />
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
              
              {currentTicket && (
                <Button 
                  onClick={handleScanKnowledgeBase}
                  disabled={isLoading}
                  variant="outline"
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Generate Response
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Knowledge Base Results */}
        {showKnowledgeBase && (
          <Card className="ml-card mb-8 ml-scale-in">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Lightbulb className="w-6 h-6 text-ml-warning" />
                <span>Knowledge Base Results</span>
              </CardTitle>
              <CardDescription>
                Similar tickets and suggested responses from the knowledge base
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-border rounded-lg">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="border border-border p-3 text-left font-semibold">Description</th>
                        <th className="border border-border p-3 text-left font-semibold">Public Log</th>
                      </tr>
                    </thead>
                    <tbody>
                      {knowledgeBaseData.map((item, index) => (
                        <tr key={index} className="hover:bg-muted/30">
                          <td className="border border-border p-3">{item.description}</td>
                          <td className="border border-border p-3">{item.publicLog}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="generic-response">Generated Response</Label>
                  <Textarea
                    id="generic-response"
                    value={response}
                    onChange={(e) => setResponse(e.target.value)}
                    className="min-h-[200px]"
                    placeholder="Generated response will appear here..."
                  />
                </div>

                <div className="flex flex-wrap gap-3 justify-center pt-4">
                  <Button 
                    onClick={() => handleLabelAction("Confirm")}
                    className="ml-button-primary"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Confirm Response
                  </Button>
                  
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline">
                        <Edit3 className="w-4 h-4 mr-2" />
                        Edit Response
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Edit Response</DialogTitle>
                        <DialogDescription>
                          Modify the response to better match the ticket requirements
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <Textarea
                          value={response}
                          onChange={(e) => setResponse(e.target.value)}
                          className="min-h-[300px]"
                        />
                        <div className="flex space-x-2 justify-end">
                          <Button variant="outline">Cancel</Button>
                          <Button className="ml-button-primary">Save Changes</Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Button 
                    onClick={() => handleLabelAction("Reject")}
                    variant="destructive"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject Response
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Guidelines */}
        <Card className="ml-card ml-fade-in">
          <CardHeader>
            <CardTitle>Response Labeling Guidelines</CardTitle>
            <CardDescription>Best practices for resolution labeling</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2 text-ml-success">✓ Do</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• Verify response addresses the user's specific request</li>
                  <li>• Check for appropriate tone and professionalism</li>
                  <li>• Ensure all necessary information is included</li>
                  <li>• Validate links and references work correctly</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2 text-ml-error">✗ Don't</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• Use generic responses for specific technical issues</li>
                  <li>• Include placeholder information without verification</li>
                  <li>• Ignore the user's context and background</li>
                  <li>• Skip proofreading for clarity and accuracy</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResolutionLabeling;