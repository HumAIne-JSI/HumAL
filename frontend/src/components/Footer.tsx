import { Link } from "react-router-dom";
import { Brain, BookOpen, Zap, Github, Mail, ExternalLink } from "lucide-react";
import HumaineLogo from "./HumaineLogo";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const navLinks = [
    { path: "/", label: "Home", icon: Brain },
    { path: "/training", label: "Model Training", icon: BookOpen },
    { path: "/dispatch-labeling", label: "Dispatch Labeling", icon: BookOpen },
    { path: "/resolution-labeling", label: "Resolution Labeling", icon: BookOpen },
    { path: "/inference", label: "Inference", icon: Zap },
  ];

  return (
    <footer className="bg-card/50 backdrop-blur-sm border-t border-border mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <HumaineLogo width={150} height={45} className="text-primary" />
            </div>
            <p className="text-muted-foreground max-w-md mb-4">
              Advanced machine learning platform for intelligent ticket classification and routing using active learning algorithms.
            </p>
            <div className="flex space-x-4">
              <a
                href="mailto:contact@humaine.ai"
                className="text-muted-foreground hover:text-primary transition-colors"
                aria-label="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
              <a
                href="https://github.com/humaine"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="https://humaine.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                aria-label="Website"
              >
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Navigation Links */}
          <div>
            <h4 className="font-semibold mb-4">Platform</h4>
            <ul className="space-y-2">
              {navLinks.map(({ path, label, icon: Icon }) => (
                <li key={path}>
                  <Link
                    to={path}
                    className="text-muted-foreground hover:text-primary transition-colors flex items-center space-x-2 text-sm"
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="text-muted-foreground hover:text-primary transition-colors text-sm"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-muted-foreground hover:text-primary transition-colors text-sm"
                >
                  API Reference
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-muted-foreground hover:text-primary transition-colors text-sm"
                >
                  Support
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-muted-foreground hover:text-primary transition-colors text-sm"
                >
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-border pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-muted-foreground">
              © {currentYear} HumAIne. All rights reserved.
            </p>
            <p className="text-sm text-muted-foreground mt-2 md:mt-0">
              Built with ❤️ using Active Learning
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;