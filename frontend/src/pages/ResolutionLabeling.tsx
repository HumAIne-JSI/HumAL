import { useState, useEffect } from "react";
import { MessageSquare, Send, Check, Edit3, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiService } from "@/services/api";

interface SimilarTicket {
  ref: string;
  team: string;
  similarity: number;
  title: string;
  description: string;
  service: string;
  subcategory: string;
}

interface ResolutionPrediction {
  classification: string;
  team: string;
  response: string;
  similar_tickets: SimilarTicket[];
}

const ResolutionLabeling = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<ResolutionPrediction | null>(null);
  const [isEditingResponse, setIsEditingResponse] = useState(false);
  const [editedResponse, setEditedResponse] = useState("");
  const [expandedTickets, setExpandedTickets] = useState<Set<number>>(new Set());
  const [formData, setFormData] = useState({
    service: "",
    subcategory: "",
    title: "",
    description: ""
  });
  const { toast } = useToast();

  // Available categories and subcategories from API
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [availableSubcategories, setAvailableSubcategories] = useState<string[]>([]);

  // Fetch categories and subcategories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const trainDataPath = "data/al_demo_train_data.csv";
        const categoriesResponse = await apiService.getCategories(0, trainDataPath);
        if (categoriesResponse.success && categoriesResponse.data) {
          setAvailableCategories(categoriesResponse.data.categories);
        }
      } catch (error) {
        console.error("Failed to load categories:", error);
      }
    };

    const fetchSubcategories = async () => {
      try {
        const trainDataPath = "data/al_demo_train_data.csv";
        const subcategoriesResponse = await apiService.getSubcategories(0, trainDataPath);
        if (subcategoriesResponse.success && subcategoriesResponse.data) {
          setAvailableSubcategories(subcategoriesResponse.data.subcategories);
        }
      } catch (error) {
        console.error("Failed to load subcategories:", error);
      }
    };

    fetchCategories();
    fetchSubcategories();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setIsLoading(true);
    setPrediction(null);
    setIsEditingResponse(false);
    
    try {
      // Simulate API call with loading state
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock response data
      const mockPrediction: ResolutionPrediction = {
        classification: "license_request",
        team: "IT Access Management",
        response: `Dear user,

your ${formData.title.toLowerCase().includes('jira') ? 'Jira' : 'software'} license has been successfully assigned.
You can verify your assigned licenses at the following portal: [license portal link].

Please note:

The license grants access to the application.

To work on a specific project or space, additional permissions may be required.

These project/space-level permissions are managed directly by the respective project administrators.

If you encounter any issues with access or functionality, please reopen the ticket or contact your project manager/project administrator.

Best regards,
Service Desk`,
        similar_tickets: [
          {
            ref: "INC0012345",
            team: "IT Access Management",
            similarity: 0.92,
            title: "Jira license request for project access",
            description: "I need a Jira license to access the project Agile Transformation and track my development tasks",
            service: "IT Services",
            subcategory: "Access Request"
          },
          {
            ref: "INC0012346",
            team: "IT Access Management",
            similarity: 0.87,
            title: "Request for collaboration tool access",
            description: "Requesting a Jira license to collaborate with my team on the Customer Onboarding project",
            service: "IT Services",
            subcategory: "License Management"
          },
          {
            ref: "INC0012347",
            team: "IT Access Management",
            similarity: 0.81,
            title: "Project management tool license needed",
            description: "Need Jira access for Digital Banking initiative project management",
            service: "IT Services",
            subcategory: "Access Request"
          }
        ]
      };

      setPrediction(mockPrediction);
      setEditedResponse(mockPrediction.response);

      toast({
        title: "Resolution Generated",
        description: `Ticket resolved and assigned to ${mockPrediction.team}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate resolution",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmResolution = () => {
    toast({
      title: "Resolution Confirmed",
      description: "The resolution has been saved successfully.",
    });
    
    // Reset form and state
    setFormData({
      service: "",
      subcategory: "",
      title: "",
      description: ""
    });
    setPrediction(null);
    setIsEditingResponse(false);
    setEditedResponse("");
    setExpandedTickets(new Set());
  };

  const toggleTicketExpansion = (index: number) => {
    const newExpanded = new Set(expandedTickets);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedTickets(newExpanded);
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8 ml-fade-in">
          <h1 className="text-4xl font-bold mb-4">
            <span className="ml-hero-text">Ticket Resolution Interface</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Generate automated responses for IT support tickets using AI-powered resolution
          </p>
        </div>

        {/* Input Form */}
        <Card className="ml-card mb-8 ml-fade-in">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="w-6 h-6 text-primary" />
              <span>Ticket Information</span>
            </CardTitle>
            <CardDescription>
              Enter ticket details to generate an automated resolution
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Service Selection */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="service">Service Category</Label>
                  <Select 
                    value={formData.service} 
                    onValueChange={(value) => setFormData({...formData, service: value, subcategory: ""})}
                    disabled={availableCategories.length === 0}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={availableCategories.length === 0 ? "No categories available" : "Select a service"} />
                    </SelectTrigger>
                    <SelectContent>
                      {availableCategories.map((category) => (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="subcategory">Service Subcategory</Label>
                  <Select 
                    value={formData.subcategory} 
                    onValueChange={(value) => setFormData({...formData, subcategory: value})}
                    disabled={!formData.service || availableSubcategories.length === 0}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={availableSubcategories.length === 0 ? "No subcategories available" : "Select a subcategory"} />
                    </SelectTrigger>
                    <SelectContent>
                      {availableSubcategories.map((subcategory) => (
                        <SelectItem key={subcategory} value={subcategory}>
                          {subcategory}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Title and Description */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Ticket Title</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    placeholder="Enter ticket title"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Ticket Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Enter detailed ticket description"
                    className="min-h-[120px]"
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button 
                type="submit"
                disabled={isLoading}
                className="ml-button-primary w-full md:w-auto"
              >
                {isLoading ? (
                  <>
                    <div className="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                    Generating Resolution...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Generate Resolution
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Resolution Results */}
        {prediction && (
          <Card className="ml-card mb-8 ml-scale-in">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Check className="w-6 h-6 text-ml-success" />
                <span>Generated Resolution</span>
              </CardTitle>
              <CardDescription>
                AI-generated response based on similar historical tickets
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Team Assignment */}
              <div className="p-4 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Assigned Team</p>
                    <h3 className="text-xl font-bold">{prediction.team}</h3>
                  </div>
                  <Badge variant="secondary" className="text-sm">
                    {prediction.classification}
                  </Badge>
                </div>
              </div>

              {/* Generated Response */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="resolution-response">Suggested Response</Label>
                  {!isEditingResponse && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditingResponse(true)}
                    >
                      <Edit3 className="w-4 h-4 mr-2" />
                      Edit Response
                    </Button>
                  )}
                </div>
                <Textarea
                  id="resolution-response"
                  value={editedResponse}
                  onChange={(e) => setEditedResponse(e.target.value)}
                  className="min-h-[250px]"
                  readOnly={!isEditingResponse}
                />
                {isEditingResponse && (
                  <p className="text-sm text-muted-foreground">
                    Editing enabled. Modify the response as needed before confirming.
                  </p>
                )}
              </div>

              {/* Similar Tickets */}
              {prediction.similar_tickets && prediction.similar_tickets.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold">Similar Historical Tickets</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    These tickets were used to generate the suggested response
                  </p>
                  
                  <div className="space-y-3">
                    {prediction.similar_tickets.map((ticket, index) => (
                      <div 
                        key={index}
                        className="border rounded-lg overflow-hidden transition-all"
                      >
                        {/* Ticket Header - Always Visible */}
                        <div 
                          className="p-4 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                          onClick={() => toggleTicketExpansion(index)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3 flex-1">
                              <Badge variant="outline">{ticket.ref}</Badge>
                              <span className="text-sm font-medium">{ticket.team}</span>
                              <Badge 
                                variant="secondary"
                                className={ticket.similarity > 0.85 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}
                              >
                                {(ticket.similarity * 100).toFixed(1)}% similar
                              </Badge>
                            </div>
                            {expandedTickets.has(index) ? (
                              <ChevronUp className="w-5 h-5 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-muted-foreground" />
                            )}
                          </div>
                        </div>

                        {/* Ticket Details - Expandable */}
                        {expandedTickets.has(index) && (
                          <div className="p-4 border-t bg-background space-y-3 ml-scale-in">
                            <div className="flex items-center space-x-2 mb-3">
                              <Badge variant="secondary">{ticket.service}</Badge>
                              <Badge variant="outline">{ticket.subcategory}</Badge>
                            </div>
                            
                            <div>
                              <span className="text-xs font-medium text-muted-foreground">Title:</span>
                              <p className="text-sm mt-1">{ticket.title}</p>
                            </div>
                            
                            <div>
                              <span className="text-xs font-medium text-muted-foreground">Description:</span>
                              <Textarea
                                value={ticket.description}
                                readOnly
                                className="mt-1 min-h-[80px] resize-none text-sm"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirm Button */}
              <div className="pt-4">
                <Button 
                  onClick={handleConfirmResolution}
                  className="ml-button-primary w-full"
                >
                  <Check className="w-4 h-4 mr-2" />
                  Confirm Resolution
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Example Tickets */}
        <Card className="ml-card ml-fade-in">
          <CardHeader>
            <CardTitle>Example Tickets</CardTitle>
            <CardDescription>Try these sample tickets to see the resolution system in action</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-muted/30 rounded-lg">
                <h4 className="font-semibold mb-2">Jira License Request</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  "I need a Jira license to access the project Agile Transformation and track my development tasks"
                </p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    const firstCategory = availableCategories[0] || "";
                    const firstSubcategory = availableSubcategories[0] || "";
                    setFormData({
                      service: firstCategory,
                      subcategory: firstSubcategory,
                      title: "Jira License Request",
                      description: "I need a Jira license to access the project Agile Transformation and track my development tasks"
                    });
                  }}
                >
                  Use This Example
                </Button>
              </div>
              
              <div className="p-4 bg-muted/30 rounded-lg">
                <h4 className="font-semibold mb-2">VPN Access Issue</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  "I cannot connect to the corporate VPN from my home network. Getting connection timeout errors."
                </p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    const firstCategory = availableCategories[0] || "";
                    const firstSubcategory = availableSubcategories[0] || "";
                    setFormData({
                      service: firstCategory,
                      subcategory: firstSubcategory,
                      title: "VPN Connection Timeout",
                      description: "I cannot connect to the corporate VPN from my home network. Getting connection timeout errors."
                    });
                  }}
                >
                  Use This Example
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResolutionLabeling;
