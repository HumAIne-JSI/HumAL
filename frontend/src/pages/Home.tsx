import { Link } from "react-router-dom";
import { Brain, BookOpen, Zap, ArrowRight, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const Home = () => {
  const features = [
    {
      title: "Model Training",
      description: "Create and configure active learning models with various algorithms and querying strategies.",
      icon: Brain,
      path: "/training",
      color: "from-blue-500 to-purple-600",
    },
    {
      title: "Dispatch Labeling",
      description: "Review and confirm team assignments for support tickets to train dispatch models.",
      icon: Users,
      path: "/dispatch-labeling",
      color: "from-blue-500 to-cyan-600",
    },
    {
      title: "Ticket Resolution",
      description: "Generate and refine AI-powered resolutions for support tickets.",
      icon: BookOpen,
      path: "/ticket-resolution",
      color: "from-purple-500 to-pink-600",
    },
    {
      title: "Inference",
      description: "Get automatic predictions for ticket classification using your trained models.",
      icon: Zap,
      path: "/inference",
      color: "from-green-500 to-blue-600",
    },
  ];

  return (
    <div className="min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16 ml-fade-in">
          <h1 className="text-5xl font-bold mb-6">
            <span className="ml-hero-text">Smart Ticketing System</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Harness the power of active machine learning to automatically classify and route support tickets. 
            Build intelligent models that learn from your feedback and improve over time.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild className="ml-button-primary text-lg px-8 py-3">
              <Link to="/training">
                <Brain className="w-5 h-5 mr-2" />
                Start Training
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
            </Button>
            <Button asChild variant="outline" className="text-lg px-8 py-3">
              <Link to="/inference">
                Try Inference
                <Zap className="w-5 h-5 ml-2" />
              </Link>
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {features.map(({ title, description, icon: Icon, path, color }, index) => (
            <Card 
              key={title} 
              className={`ml-card hover:scale-105 transition-all duration-300 ml-fade-in`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <CardHeader className="text-center">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r ${color} flex items-center justify-center`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <CardTitle className="text-xl font-semibold">{title}</CardTitle>
                <CardDescription className="text-base">
                  {description}
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <Button asChild className="ml-button-primary w-full">
                  <Link to={path}>
                    Get Started
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stats Section */}
        <div className="bg-card/50 backdrop-blur-sm rounded-lg p-8 mb-12 ml-fade-in">
          <h2 className="text-3xl font-bold text-center mb-8">Why Active Learning?</h2>
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold ml-hero-text mb-2">85%</div>
              <p className="text-muted-foreground">Reduction in labeling effort</p>
            </div>
            <div>
              <div className="text-4xl font-bold ml-hero-text mb-2">3x</div>
              <p className="text-muted-foreground">Faster model convergence</p>
            </div>
            <div>
              <div className="text-4xl font-bold ml-hero-text mb-2">95%</div>
              <p className="text-muted-foreground">Classification accuracy</p>
            </div>
          </div>
        </div>

        {/* How it Works */}
        <div className="text-center ml-fade-in">
          <h2 className="text-3xl font-bold mb-8">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="space-y-4">
              <div className="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
                1
              </div>
              <h3 className="text-xl font-semibold">Train Your Model</h3>
              <p className="text-muted-foreground">
                Configure active learning parameters and create your first model instance
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
                2
              </div>
              <h3 className="text-xl font-semibold">Label Smart Samples</h3>
              <p className="text-muted-foreground">
                The system intelligently selects the most informative tickets for you to label
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 mx-auto bg-primary rounded-full flex items-center justify-center text-white font-bold text-xl">
                3
              </div>
              <h3 className="text-xl font-semibold">Get Predictions</h3>
              <p className="text-muted-foreground">
                Use your trained model to automatically classify new support tickets
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;