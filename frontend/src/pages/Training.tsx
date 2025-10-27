import { useState, useEffect } from "react";
import { Brain, Settings, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { apiService } from "@/services/api";

const Training = () => {
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [instanceId, setInstanceId] = useState<number | null>(null);
  const { toast } = useToast();

  // State for available models and strategies from API
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);

  const [config, setConfig] = useState({
    model: "",
    strategy: "",
    task: "dispatch" as "dispatch" | "resolution"
  });

  // Fetch available models, strategies, and teams on component mount
  useEffect(() => {
    const fetchConfig = async () => {
      setIsLoadingConfig(true);
      try {
        const trainDataPath = "data/al_demo_train_data.csv";
        const [modelsResponse, strategiesResponse, teamsResponse] = await Promise.all([
          apiService.getModels(),
          apiService.getQueryStrategies(),
          apiService.getTeams(0, trainDataPath)
        ]);

        if (modelsResponse.success && modelsResponse.data) {
          setAvailableModels(modelsResponse.data.models);
          // Set first model as default
          if (modelsResponse.data.models.length > 0) {
            setConfig(prev => ({ ...prev, model: modelsResponse.data.models[0] }));
          }
        }

        if (strategiesResponse.success && strategiesResponse.data) {
          setAvailableStrategies(strategiesResponse.data.strategies);
          // Set first strategy as default
          if (strategiesResponse.data.strategies.length > 0) {
            setConfig(prev => ({ ...prev, strategy: strategiesResponse.data.strategies[0] }));
          }
        }

        if (teamsResponse.success && teamsResponse.data) {
          setTeams(teamsResponse.data.teams);
        }
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to load configuration options",
          variant: "destructive",
        });
      } finally {
        setIsLoadingConfig(false);
      }
    };

    fetchConfig();
  }, []);

  const handleCreateInstance = async () => {
    setIsLoading(true);
    
    try {
      // Call the actual API endpoint
      const response = await apiService.createInstance({
        model_name: config.model,
        qs_strategy: config.strategy,
        class_list: teams, // Use teams from /data/teams endpoint
        train_data_path: "data/al_demo_train_data.csv",
        test_data_path: "data/al_demo_test_data.csv",
        al_type: config.task
      });

      if (response.success && response.data) {
        setInstanceId(response.data.instance_id);
        
        toast({
          title: "Success!",
          description: `Active learning instance created with ID: ${response.data.instance_id}`,
        });
      } else {
        throw new Error(response.error?.detail || "Failed to create instance");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create active learning instance",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to format display names
  const formatDisplayName = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8 ml-fade-in">
          <h1 className="text-4xl font-bold mb-4">
            <span className="ml-hero-text">Active Learning Model Training</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Create and configure your machine learning models for smart ticket classification
          </p>
        </div>

        {/* Main Card */}
        <Card className="ml-card mb-8 ml-fade-in">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Brain className="w-6 h-6 text-primary" />
              <span>Create Active Learning Instance</span>
            </CardTitle>
            <CardDescription>
              Configure your model parameters to get started with active learning
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Basic Configuration</h3>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="task">Task Type</Label>
                  <Select value={config.task} onValueChange={(value: "dispatch" | "resolution") => setConfig({...config, task: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select task type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dispatch">Dispatch</SelectItem>
                      <SelectItem value="resolution">Resolution</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            <Collapsible open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-start">
                  <Settings className="w-4 h-4 mr-2" />
                  Advanced Settings
                  <span className="ml-auto">{isAdvancedOpen ? "−" : "+"}</span>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 mt-4 p-4 bg-muted/30 rounded-lg">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="model">Model Algorithm</Label>
                    <Select 
                      value={config.model} 
                      onValueChange={(value) => setConfig({...config, model: value})}
                      disabled={isLoadingConfig}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={isLoadingConfig ? "Loading..." : "Select model"} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableModels.map((model) => (
                          <SelectItem key={model} value={model}>
                            {formatDisplayName(model)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="strategy">Querying Strategy</Label>
                    <Select 
                      value={config.strategy} 
                      onValueChange={(value) => setConfig({...config, strategy: value})}
                      disabled={isLoadingConfig}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={isLoadingConfig ? "Loading..." : "Select strategy"} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableStrategies.map((strategy) => (
                          <SelectItem key={strategy} value={strategy}>
                            {formatDisplayName(strategy)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Strategy Explanation</h4>
                  <div className="text-sm text-muted-foreground space-y-1">
                    {config.strategy === "random sampling" && (
                      <p>Randomly selects samples for labeling. Good baseline but not optimal for learning efficiency.</p>
                    )}
                    {config.strategy === "uncertainty sampling entropy" && (
                      <p>Selects samples with highest prediction entropy. Focuses on the most uncertain predictions.</p>
                    )}
                    {config.strategy === "uncertainty sampling margin sampling" && (
                      <p>Selects samples with smallest margin between top two predictions. Good for binary classification.</p>
                    )}
                    {config.strategy === "uncertainty sampling least confidence" && (
                      <p>Selects samples with lowest confidence in the top prediction. Conservative approach.</p>
                    )}
                    {config.strategy === "CLUE" && (
                      <p>Clustering-based Uncertainty sampling with Entropy for diverse instance selection.</p>
                    )}
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Create Button */}
            <div className="pt-4">
              <Button 
                onClick={handleCreateInstance}
                disabled={isLoading || isLoadingConfig}
                className="ml-button-primary w-full md:w-auto"
              >
                {isLoading ? (
                  <>
                    <div className="ml-pulse w-4 h-4 mr-2 bg-white rounded-full" />
                    Creating Instance...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Active Learning Instance
                  </>
                )}
              </Button>
            </div>

            {/* Success Message */}
            {instanceId && (
              <div className="mt-6 p-4 bg-ml-success/10 border border-ml-success/20 rounded-lg ml-scale-in">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-ml-success rounded-full flex items-center justify-center flex-shrink-0">
                    <Brain className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-ml-success">Instance Created Successfully!</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Your active learning instance has been created with ID: <code className="px-2 py-1 bg-muted rounded text-xs">{instanceId}</code>
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      You can now proceed to the labeling page to start training your model with sample tickets.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Configuration Summary */}
        <Card className="ml-card ml-fade-in">
          <CardHeader>
            <CardTitle>Current Configuration</CardTitle>
            <CardDescription>Review your model settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Task</div>
                <div className="mt-1 text-lg font-bold capitalize">{config.task}</div>
              </div>
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Model</div>
                <div className="mt-1 text-lg font-bold capitalize">{formatDisplayName(config.model)}</div>
              </div>
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Strategy</div>
                <div className="mt-1 text-sm font-bold capitalize">{formatDisplayName(config.strategy)}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Training;
