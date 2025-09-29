import { useState, useEffect } from "react";
import { Zap, Send, Brain, HelpCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const Inference = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [formData, setFormData] = useState({
    service: "",
    subcategory: "",
    title: "",
    description: ""
  });
  const { toast } = useToast();

  // Mock available models (latest first)
  const availableModels = [
    {
      id: "al_inference_1729789012",
      name: "Ticket Classification Model v3.2",
      accuracy: 94.8,
      status: "active",
      createdAt: "2024-10-24T14:30:12Z"
    },
    {
      id: "al_inference_1729702612",
      name: "Ticket Classification Model v3.1",
      accuracy: 92.1,
      status: "active",
      createdAt: "2024-10-23T14:30:12Z"
    },
    {
      id: "al_inference_1729616212",
      name: "Ticket Classification Model v3.0",
      accuracy: 89.7,
      status: "archived",
      createdAt: "2024-10-22T14:30:12Z"
    }
  ];

  // Auto-select the latest model on component mount
  useEffect(() => {
    if (availableModels.length > 0) {
      setSelectedModel(availableModels[0].id);
    }
  }, []);

  const services = [
    { value: "it-support", label: "IT Support" },
    { value: "hr", label: "Human Resources" },
    { value: "finance", label: "Finance" },
    { value: "facilities", label: "Facilities" }
  ];

  const subcategories = {
    "it-support": [
      { value: "software", label: "Software Issues" },
      { value: "hardware", label: "Hardware Issues" },
      { value: "access", label: "Access Management" },
      { value: "email", label: "Email & Communication" }
    ],
    "hr": [
      { value: "benefits", label: "Benefits & Compensation" },
      { value: "policies", label: "HR Policies" },
      { value: "training", label: "Training & Development" }
    ],
    "finance": [
      { value: "expenses", label: "Expense Reports" },
      { value: "invoicing", label: "Invoicing" },
      { value: "budget", label: "Budget Requests" }
    ],
    "facilities": [
      { value: "maintenance", label: "Maintenance Requests" },
      { value: "security", label: "Security Access" },
      { value: "supplies", label: "Office Supplies" }
    ]
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedModel) {
      toast({
        title: "Error",
        description: "Please select a model before classifying the ticket",
        variant: "destructive",
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const selectedModelInfo = availableModels.find(m => m.id === selectedModel);
      
      // Mock prediction result based on selected model
      const mockPrediction = {
        group: "IT Support - Access Management",
        confidence: 0.94,
        explanation: `The ticket contains keywords related to software access (Jira, license, project access) and follows typical access request patterns. ${selectedModelInfo?.name} is highly confident based on similar training examples.`,
        reasoning: [
          { factor: "Keywords", score: 0.98, details: "Jira, license, access, project" },
          { factor: "Pattern Match", score: 0.91, details: "Follows standard access request format" },
          { factor: "Service Category", score: 0.93, details: "Matches IT Support service patterns" }
        ],
        model: selectedModelInfo
      };
      
      setPrediction(mockPrediction);
      
      toast({
        title: "Prediction Complete",
        description: `Ticket classified as: ${mockPrediction.group}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get prediction from model",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "text-ml-success";
    if (confidence >= 0.7) return "text-ml-warning";
    return "text-ml-error";
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) return "default";
    if (confidence >= 0.7) return "secondary";
    return "destructive";
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8 ml-fade-in">
          <h1 className="text-4xl font-bold mb-4">
            <span className="ml-hero-text">Ticket Inference Engine</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Get automatic predictions for ticket classification using your trained models
          </p>
        </div>

        {/* Input Form */}
        <Card className="ml-card mb-8 ml-fade-in">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="w-6 h-6 text-primary" />
              <span>Ticket Classification</span>
            </CardTitle>
            <CardDescription>
              Enter ticket details to get an automatic classification prediction
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Model Selection */}
              <div className="space-y-2">
                <Label htmlFor="model">Select Inference Model</Label>
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

              {/* Service Selection */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="service">Service Category</Label>
                  <Select 
                    value={formData.service} 
                    onValueChange={(value) => setFormData({...formData, service: value, subcategory: ""})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a service" />
                    </SelectTrigger>
                    <SelectContent>
                      {services.map((service) => (
                        <SelectItem key={service.value} value={service.value}>
                          {service.label}
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
                    disabled={!formData.service}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a subcategory" />
                    </SelectTrigger>
                    <SelectContent>
                      {formData.service && subcategories[formData.service as keyof typeof subcategories]?.map((sub) => (
                        <SelectItem key={sub.value} value={sub.value}>
                          {sub.label}
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
                    Classifying Ticket...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Classify Ticket
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Prediction Results */}
        {prediction && (
          <Card className="ml-card mb-8 ml-scale-in">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Brain className="w-6 h-6 text-ml-success" />
                <span>Classification Result</span>
              </CardTitle>
              <CardDescription>
                Model prediction for the submitted ticket
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Main Prediction */}
              <div className="text-center p-6 bg-gradient-to-r from-ml-primary/10 to-ml-secondary/10 rounded-lg">
                <h3 className="text-2xl font-bold mb-2">{prediction.group}</h3>
                <div className="flex items-center justify-center space-x-2">
                  <span className="text-muted-foreground">Confidence:</span>
                  <Badge variant={getConfidenceBadge(prediction.confidence)} className="text-lg px-3 py-1">
                    {(prediction.confidence * 100).toFixed(1)}%
                  </Badge>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <HelpCircle className="w-4 h-4" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-80">
                      <div className="space-y-2">
                        <h4 className="font-semibold">Model Explanation</h4>
                        <p className="text-sm text-muted-foreground">
                          {prediction.explanation}
                        </p>
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {/* Reasoning Breakdown */}
              <div className="space-y-4">
                <h4 className="font-semibold">Reasoning Breakdown</h4>
                <div className="space-y-3">
                  {prediction.reasoning.map((item: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                      <div>
                        <div className="font-medium">{item.factor}</div>
                        <div className="text-sm text-muted-foreground">{item.details}</div>
                      </div>
                      <div className={`font-bold ${getConfidenceColor(item.score)}`}>
                        {(item.score * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3 justify-center pt-4">
                <Button className="ml-button-primary">
                  Accept Classification
                </Button>
                <Button variant="outline">
                  Provide Feedback
                </Button>
                <Button variant="outline">
                  View Similar Cases
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Examples */}
        <Card className="ml-card ml-fade-in">
          <CardHeader>
            <CardTitle>Example Tickets</CardTitle>
            <CardDescription>Try these sample tickets to see the model in action</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-muted/30 rounded-lg">
                <h4 className="font-semibold mb-2">IT Access Request</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  "I need a Jira license to access the project Agile Transformation and track my development tasks"
                </p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setFormData({
                    ...formData,
                    title: "Jira License Request",
                    description: "I need a Jira license to access the project Agile Transformation and track my development tasks",
                    service: "it-support",
                    subcategory: "access"
                  })}
                >
                  Use This Example
                </Button>
              </div>
              
              <div className="p-4 bg-muted/30 rounded-lg">
                <h4 className="font-semibold mb-2">Hardware Issue</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  "My laptop screen is flickering and sometimes goes black. It's affecting my productivity."
                </p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setFormData({
                    ...formData,
                    title: "Laptop Screen Issue",
                    description: "My laptop screen is flickering and sometimes goes black. It's affecting my productivity.",
                    service: "it-support",
                    subcategory: "hardware"
                  })}
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

export default Inference;