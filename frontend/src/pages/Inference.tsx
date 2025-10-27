import { useState, useEffect, useRef } from "react";
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
import { apiService } from "@/services/api";

const Inference = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
  const [explanationTopWords, setExplanationTopWords] = useState<[string, number][] | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(undefined);
  const [formData, setFormData] = useState({
    service: "",
    subcategory: "",
    title: "",
    description: ""
  });
  const { toast } = useToast();
  
  // Track the current prediction ID to prevent stale LIME explanations
  const currentPredictionIdRef = useRef<number>(0);

  // Available models from API
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  
  // Available categories and subcategories from API
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [availableSubcategories, setAvailableSubcategories] = useState<string[]>([]);

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
            
            // Only process dispatch models (same as dispatch labeling page)
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
        toast({
          title: "Error",
          description: "Failed to load available models",
          variant: "destructive",
        });
      }
    };

    const fetchCategories = async () => {
      try {
        // Use instance ID 0 with train data path before instance is created
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
        // Use instance ID 0 with train data path before instance is created
        const trainDataPath = "data/al_demo_train_data.csv";
        const subcategoriesResponse = await apiService.getSubcategories(0, trainDataPath);
        if (subcategoriesResponse.success && subcategoriesResponse.data) {
          setAvailableSubcategories(subcategoriesResponse.data.subcategories);
        }
      } catch (error) {
        console.error("Failed to load subcategories:", error);
      }
    };

    fetchModels();
    fetchCategories();
    fetchSubcategories();
  }, []);

  useEffect(() => {
    // If models are loaded and no model is selected yet, pick the first one.
    // We depend on availableModels so this runs *after* the fetch finishes.
    if (availableModels.length > 0 && !selectedModel) {
      setSelectedModel(availableModels[0].id);
      console.log("Auto-selected model:", availableModels[0].id);
    }
  }, [availableModels, selectedModel]);

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
    
    // Increment prediction ID to invalidate any pending LIME requests
    currentPredictionIdRef.current += 1;
    const thisPredictionId = currentPredictionIdRef.current;
    
    setIsLoading(true);
    setExplanationTopWords(null);
    
    try {
      // Build inference payload
      const inferenceData = {
        service_subcategory_name: formData.subcategory,
        service_name: formData.service,
        title_anon: formData.title,
        description_anon: formData.description,
        team_name: undefined,
        last_team_id_name: undefined,
        public_log_anon: undefined
      };

      // Call real inference endpoint
      const inferRes = await apiService.infer(parseInt(selectedModel), inferenceData);
      if (!inferRes.success || !inferRes.data) {
        if (inferRes.error?.detail?.includes("not trained yet")) {
          toast({ title: "Model not trained", description: "Please train the model first.", variant: "destructive" });
          return;
        }
        throw new Error(inferRes.error?.detail || "Failed to get prediction from model");
      }

      const selectedModelInfo = availableModels.find(m => m.id === selectedModel);
      // Backend returns array of predictions; extract first element
      const predictedGroup = Array.isArray(inferRes.data) ? inferRes.data[0] : inferRes.data.prediction;

      // Set immediate prediction (no confidence shown)
      setPrediction({
        group: String(predictedGroup),
        explanation: `Prediction generated by ${selectedModelInfo?.name}.`,
        model: selectedModelInfo
      });

      toast({
        title: "Prediction Complete",
        description: `Ticket classified as: ${String(predictedGroup)}`,
      });

      // Fire-and-forget LIME explanation; show reasoning once it arrives
      (async () => {
        try {
          const explainRes = await apiService.explainLime(parseInt(selectedModel), {
            ticket_data: inferenceData,
            model_id: 0
          });
          
          // Only update if this is still the current prediction
          if (thisPredictionId === currentPredictionIdRef.current && explainRes.success && explainRes.data && explainRes.data.length > 0) {
            const item = explainRes.data[0];
            if (item && Array.isArray(item.top_words)) {
              setExplanationTopWords(item.top_words);
            }
          }
        } catch (err) {
          console.error("Explain LIME failed", err);
        }
      })();
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

                <Select
                  // key causes remount when availableModels[0].id changes (prevents stale UI)
                  key={availableModels.length > 0 ? `models-${availableModels[0].id}` : "no-models"}
                  value={selectedModel ?? undefined}              // use undefined for "no value"
                  onValueChange={(val) => setSelectedModel(val)}
                  disabled={availableModels.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={availableModels.length === 0 ? "No models available" : "-- Select a Model --"}
                    />
                  </SelectTrigger>

                  <SelectContent>
                    {availableModels.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex items-center justify-between w-full min-w-0">
                          <div className="flex items-center space-x-2">
                            <span>{model.name}</span>
                            <Badge variant={model.status === 'active' ? 'default' : 'secondary'} className="text-xs">
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
                {isLoading ? (
                  <div className="space-y-3">
                    <div className="ml-pulse w-8 h-8 mx-auto bg-primary rounded-full" />
                    <p className="text-muted-foreground">Analyzing ticket content...</p>
                  </div>
                ) : (
                  <>
                    <h3 className="text-2xl font-bold mb-2">{prediction.group}</h3>
                    <p className="text-muted-foreground mb-3">Predicted classification</p>
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
                  {explanationTopWords && (
                    <div className="p-4 bg-muted/30 rounded-lg">
                      <h4 className="font-semibold mb-2">Reasoning</h4>
                      <p className="text-sm text-muted-foreground mb-2">{prediction.explanation}</p>
                      <div className="flex flex-wrap gap-2">
                        {explanationTopWords.slice(0, 10).map(([word, weight], idx) => (
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
                </>
              )}
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
                  onClick={() => {
                    const firstCategory = availableCategories[0] || "";
                    const firstSubcategory = availableSubcategories[0] || "";
                    setFormData({
                      ...formData,
                      title: "Jira License Request",
                      description: "I need a Jira license to access the project Agile Transformation and track my development tasks",
                      service: firstCategory,
                      subcategory: firstSubcategory
                    });
                  }}
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
                  onClick={() => {
                    const firstCategory = availableCategories[0] || "";
                    const firstSubcategory = availableSubcategories[0] || "";
                    setFormData({
                      ...formData,
                      title: "Laptop Screen Issue",
                      description: "My laptop screen is flickering and sometimes goes black. It's affecting my productivity.",
                      service: firstCategory,
                      subcategory: firstSubcategory
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

export default Inference;