import { useState } from "react";
import { Brain, Settings, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const Training = () => {
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [instanceId, setInstanceId] = useState<string | null>(null);
  const { toast } = useToast();

  const [config, setConfig] = useState({
    model: "random forest",
    strategy: "uncertainty sampling entropy",
    task: "dispatch"
  });

  const handleCreateInstance = async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const newInstanceId = `al_${Date.now()}`;
      setInstanceId(newInstanceId);
      
      toast({
        title: "Success!",
        description: `Active learning instance created with ID: ${newInstanceId}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create active learning instance",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
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
                  <Select value={config.task} onValueChange={(value) => setConfig({...config, task: value})}>
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
                    <Select value={config.model} onValueChange={(value) => setConfig({...config, model: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="random forest">Random Forest</SelectItem>
                        <SelectItem value="logistic regression">Logistic Regression</SelectItem>
                        <SelectItem value="svm">Support Vector Machine</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="strategy">Querying Strategy</Label>
                    <Select value={config.strategy} onValueChange={(value) => setConfig({...config, strategy: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select strategy" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="random sampling">Random Sampling</SelectItem>
                        <SelectItem value="uncertainty sampling entropy">Uncertainty Sampling - Entropy</SelectItem>
                        <SelectItem value="uncertainty sampling margin sampling">Uncertainty Sampling - Margin</SelectItem>
                        <SelectItem value="uncertainty sampling least confidence">Uncertainty Sampling - Least Confidence</SelectItem>
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
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Create Button */}
            <div className="pt-4">
              <Button 
                onClick={handleCreateInstance}
                disabled={isLoading}
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
                <div className="mt-1 text-lg font-bold capitalize">{config.model}</div>
              </div>
              <div className="text-center p-4 bg-muted/30 rounded-lg">
                <div className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Strategy</div>
                <div className="mt-1 text-sm font-bold capitalize">{config.strategy}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Training;