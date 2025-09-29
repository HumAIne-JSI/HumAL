interface HumaineLogoProps {
  className?: string;
  width?: number;
  height?: number;
}

const HumaineLogo = ({ className = "", width = 200, height = 60 }: HumaineLogoProps) => {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 400 120"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Neural Network Pattern */}
      <g opacity="0.9">
        {/* Network nodes */}
        <circle cx="20" cy="20" r="6" fill="currentColor" className="text-ml-secondary" />
        <circle cx="45" cy="15" r="8" fill="currentColor" className="text-ml-secondary" />
        <circle cx="70" cy="25" r="5" fill="currentColor" className="text-ml-secondary" />
        <circle cx="35" cy="40" r="7" fill="currentColor" className="text-ml-secondary" />
        <circle cx="60" cy="45" r="6" fill="currentColor" className="text-ml-secondary" />
        <circle cx="25" cy="65" r="5" fill="currentColor" className="text-ml-secondary" />
        <circle cx="50" cy="70" r="7" fill="currentColor" className="text-ml-secondary" />
        
        {/* Network connections */}
        <line x1="20" y1="20" x2="45" y2="15" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="45" y1="15" x2="70" y2="25" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="20" y1="20" x2="35" y2="40" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="45" y1="15" x2="35" y2="40" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="35" y1="40" x2="60" y2="45" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="35" y1="40" x2="25" y2="65" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="60" y1="45" x2="50" y2="70" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
        <line x1="25" y1="65" x2="50" y2="70" stroke="currentColor" strokeWidth="2" className="text-ml-secondary" opacity="0.6" />
      </g>

      {/* Stylized head profile */}
      <path
        d="M 85 30 Q 95 20 110 25 Q 125 30 130 45 Q 128 60 120 70 Q 110 80 95 75 Q 85 70 85 55 Z"
        fill="currentColor"
        className="text-ml-primary"
        opacity="0.8"
      />

      {/* Text: humAIne */}
      <g className="text-ml-primary" fill="currentColor">
        {/* h */}
        <rect x="160" y="35" width="6" height="40" />
        <rect x="160" y="50" width="20" height="6" />
        <rect x="174" y="50" width="6" height="25" />
        
        {/* u */}
        <rect x="190" y="50" width="6" height="20" />
        <rect x="190" y="64" width="14" height="6" />
        <rect x="198" y="50" width="6" height="20" />
        
        {/* m */}
        <rect x="214" y="50" width="6" height="25" />
        <rect x="220" y="50" width="6" height="6" />
        <rect x="226" y="56" width="6" height="19" />
        <rect x="232" y="50" width="6" height="6" />
        <rect x="238" y="56" width="6" height="19" />
        
        {/* A */}
        <polygon points="254,75 260,35 266,75 272,75 264,50 268,50 276,75 282,75 270,35 250,35 238,75 244,75 248,50 252,50" className="text-ml-secondary" />
        
        {/* I */}
        <rect x="290" y="35" width="6" height="40" className="text-ml-secondary" />
        
        {/* n */}
        <rect x="306" y="50" width="6" height="25" />
        <rect x="306" y="50" width="14" height="6" />
        <rect x="314" y="56" width="6" height="19" />
        
        {/* e */}
        <rect x="330" y="56" width="14" height="6" />
        <rect x="330" y="50" width="6" height="25" />
        <rect x="330" y="62" width="10" height="6" />
        <rect x="330" y="69" width="14" height="6" />
      </g>

      {/* Gradient overlay for depth */}
      <defs>
        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.1" className="text-ml-primary" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0.05" className="text-ml-secondary" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#logoGradient)" />
    </svg>
  );
};

export default HumaineLogo;