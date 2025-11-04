"""
Service layer for ticket resolution using RAG and LLM generation.
"""
import os
import pickle
import json
import re
import pandas as pd
import numpy as np
import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from app.core.rag_system import RAGSystem, load_knowledge_base
from app.data_models.resolution_dm import ResolutionRequest, ResolutionResponse
from app.config.resolution_config import _OPENAI_API_KEY, _OPENAI_CLIENT_MODE, _OPENAI_INIT_ERROR, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, TEAM_MAPPING


"""
OpenAI client initialization
"""

try:
    import openai
    
    # Check OpenAI version
    openai_version = getattr(openai, '__version__', '0.0.0')
    major_version = int(openai_version.split('.')[0])
    
    if major_version >= 1:
        # New SDK style (>=1.0.0)
        from openai import OpenAI as _NewOpenAIClient
        _openai_client = _NewOpenAIClient(api_key=_OPENAI_API_KEY) if _OPENAI_API_KEY else _NewOpenAIClient()
        _OPENAI_CLIENT_MODE = "new_v1"
        
        def _chat_completion(model: str, messages: list, **kwargs) -> str:
            resp = _openai_client.chat.completions.create(model=model, messages=messages, **kwargs)
            return resp.choices[0].message.content.strip()
    else:
        # Legacy SDK (<1.0.0)
        if _OPENAI_API_KEY:
            openai.api_key = _OPENAI_API_KEY
        _OPENAI_CLIENT_MODE = "legacy_v0"
        
        def _chat_completion(model: str, messages: list, **kwargs) -> str:
            resp = openai.ChatCompletion.create(model=model, messages=messages, **kwargs)
            return resp["choices"][0]["message"]["content"].strip()
            
except ImportError:
    _OPENAI_CLIENT_MODE = "unavailable"
    _OPENAI_INIT_ERROR = "OpenAI package not installed"
    
    def _chat_completion(model: str, messages: list, **kwargs) -> str:
        return "[OpenAI unavailable - install 'openai' package]"

except Exception as init_error:
    _OPENAI_CLIENT_MODE = "error"
    _OPENAI_INIT_ERROR = str(init_error)
    
    def _chat_completion(model: str, messages: list, **kwargs) -> str:
        return f"[OpenAI error: {_OPENAI_INIT_ERROR}]"


def analyze_response_type_simple(response_text):
    """Simple analysis to determine if response is template-based or personalized"""
    if not response_text or pd.isna(response_text):
        return "unknown", 0.0
    
    text = str(response_text).lower()
    
    # Template indicators (simple keyword detection)
    template_keywords = [
        "below you will find the additional form information",
        "need: extra information needed",
        "this additional ticket is automatically created",
        "- instructions:",
        "- project manager full name:",
        "- computer name:",
        "- justification:",
        "- employee id:",
        "automatically created",
        "auto-generated",
        "this ticket has been"
    ]
    
    # Personalized indicators
    personalized_keywords = [
        "thank you for contacting",
        "i understand",
        "i will help",
        "hello",
        "dear",
        "i apologize",
        "let me check",
        "please note that",
        "i recommend",
        "thank you for your request"
    ]
    
    # Count matches
    template_score = sum(1 for keyword in template_keywords if keyword in text)
    personalized_score = sum(1 for keyword in personalized_keywords if keyword in text)
    
    # Check for structured lists (template indicator)
    dash_lines = text.count('\n-')
    if dash_lines >= 3:
        template_score += 2
    
    # Check for questions (personalized indicator)
    question_marks = text.count('?')
    if question_marks > 0:
        personalized_score += 1
    
    # Determine type
    total_score = template_score + personalized_score
    if total_score == 0:
        return "unknown", 0.0
    
    template_confidence = template_score / total_score
    
    if template_confidence > 0.6:
        return "template", template_confidence
    elif template_confidence < 0.4:
        return "personalized", 1 - template_confidence
    else:
        return "mixed", 0.5

def detect_temporal_context(title, description):
    """Detect temporal/status-update context (outages, global communications, recovery plans).

    Returns: 'temporal_update' or 'standard'
    """
    text = (str(title or "") + " " + str(description or "")).lower()

    # Patterns that indicate a system status / global communication / recovery plan
    temporal_patterns = [
        r"\byesterday\b",
        r"\bwe have sent a global communication\b",
        r"\brecovery plan\b",
        r"\bwhen .* returns to normal\b",
        r"\boutage\b",
        r"\bservice interruption\b",
        r"\bwe are currently experiencing\b",
        r"\bincident\b",
        r"\bsynertrade\b",
        r"\bsap\b",
    ]

    for pat in temporal_patterns:
        if re.search(pat, text):
            return 'temporal_update'

    return 'standard'

def analyze_ticket_context(title, description, classification):
    """Analyze ticket context for better response generation"""
    context_factors = []
    
    # Urgency indicators
    if any(word in title.lower() for word in ['urgent', 'urgente', 'asap', 'immediately']):
        context_factors.append("urgent")
    
    # Request type specific context
    if classification == 'admin_rights':
        if 'install' in description.lower():
            context_factors.append("software_installation")
        if 'java' in description.lower():
            context_factors.append("development_tools")
    
    # Team context
    if 'onboarding' in description.lower() or 'new_entry' in title.lower():
        context_factors.append("employee_onboarding")
    
    return ", ".join(context_factors) if context_factors else "standard_request"

def select_best_templates(title, description, template_examples, top_k=3):
    """Select the most similar templates based on content similarity"""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    # Create query text
    query_text = f"{title} {description}"
    
    # Create comparison texts
    comparison_texts = []
    for _, row in template_examples.iterrows():
        comp_text = f"{row.get('Title_anon', '')} {row.get('Description_anon', '')}"
        comparison_texts.append(comp_text)
    
    # Calculate similarities using sentence transformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query_text])
    comparison_embeddings = model.encode(comparison_texts)
    
    # Calculate cosine similarities
    similarities = np.dot(query_embedding, comparison_embeddings.T).flatten()
    
    # Add similarity scores and sort
    template_examples = template_examples.copy()
    template_examples['template_similarity'] = similarities
    
    return template_examples.nlargest(top_k, 'template_similarity')

def get_specific_instructions(classification, predicted_team):
    """Get specific instructions based on ticket type and team"""
    instructions = {
        'admin_rights': """
- MUST include form fields: 'Need:', 'Do you need admin rights...', 'Project Manager Full name:'
- Use EXACT structure from admin rights templates
- Include approval requirements""",
        
        'badge_access': """
- MUST start with 'Below you will find the additional form information'
- Include 'Need: Extra information needed to request office access'
- Use structured format with colleague information""",
        
        'email_support': """
- Focus on mailbox or communication issues
- Include troubleshooting steps if shown in template
- Maintain technical support format""",
        
        'software_request': """
- Include software installation requirements
- Use form structure for license/approval process
- Reference project manager requirements""",
        
        'vpn_request': """
- For onboarding: Use brief auto-generated format
- For VPN access: Include network configuration details
- Maintain structured list format"""
    }
    
    team_instructions = {
        '(BF) Information Security Office': "- Focus on security approval processes\n- Include project manager requirements",
        '(LF) IT Office Access Italy': "- Use Italian office access format\n- Include colleague contact information",
        '(GI-UX) Account Management': "- Use onboarding templates for new employees\n- Keep format brief and structured"
    }
    
    result = instructions.get(classification, "- Follow the template structure exactly")
    if predicted_team in team_instructions:
        result += f"\n{team_instructions[predicted_team]}"
    
    return result

def select_best_similar_replies(title, description, similar_replies, top_k=2):
    """Select the most relevant similar replies for better context"""
    # Already has similarity scores from RAG system
    if 'enhanced_score' in similar_replies.columns:
        return similar_replies.nlargest(top_k, 'enhanced_score')
    else:
        return similar_replies.head(top_k)

def determine_response_style(similar_replies):
    """Determine the appropriate response style based on similar replies"""
    reply_texts = [reply.get('first_reply', '') for _, reply in similar_replies.iterrows()]
    
    # Check for common patterns
    if any('Below you will find' in text for text in reply_texts):
        return "Structured form-based response"
    elif any(len(text) < 200 for text in reply_texts):
        return "Brief informational response"
    else:
        return "Detailed personalized response"


def get_template_response_for_class(predicted_class):
    """Map predicted class to appropriate template response"""
    
    template_mapping = {
        "vpn_request": "Need: Extra information needed to enable Client-to-Site VPN tunnel requests.",
        "onboarding": "Need: Extra information needed to start the IT On-boarding of a new internal employee.",
        "software_request": "Need: Extra information needed to request a software or a licence on my Windows device.",
        "software_support": "Need: Extra information needed to support you about local software / programs.",
        "admin_rights": "Need: Extra information needed to request admin rights on the computer.",
        "offboarding": "Need: Extra information needed to start the IT Off-boarding process.",
        "absence_request": "Need: Extra information needed to request an Absence ticket.",
        "badge_access": "Need: Extra information needed to request office access.",
        "email_support": "Need: Extra information needed to support you with email/mailbox issues.",
        "password_reset": "Need: Extra information needed to reset your password.",
        "printer_support": "Need: Extra information needed to support you with printer issues.",
        "hardware_support": "Need: Extra information needed to support you with hardware issues.",
        "other": "Thank you for your request. I will review the details and get back to you shortly."
    }
    
    return template_mapping.get(predicted_class, "Thank you for your request. I will review the details and get back to you shortly.")

def classify_ticket_with_keywords(ticket_text, service_category=None, service_subcategory=None):
    """Keyword-based classification as fallback"""
    
    text_lower = ticket_text.lower()
    
    # VPN requests (most specific first)
    if any(word in text_lower for word in ['vpn', 'tunnel', 'remote access', 'client-to-site', 'network access']):
        return "vpn_request", "Need: Extra information needed to enable Client-to-Site VPN tunnel requests."
    
    # Employee onboarding
    elif any(word in text_lower for word in ['onboard', 'new employee', 'employee setup', 'employee starting', 'employee id', 'missing employee']):
        return "onboarding", "Need: Extra information needed to start the IT On-boarding of a new internal employee."
    
    # Software installation vs support
    elif any(word in text_lower for word in ['install', 'installation', 'need software']) and not any(word in text_lower for word in ['support', 'help', 'issue', 'problem']):
        return "software_request", "Need: Extra information needed to request a software or a licence on my Windows device."
    
    # Software support
    elif any(word in text_lower for word in ['software support', 'software help', 'software issue', 'help with', 'issue with']):
        return "software_support", "Need: Extra information needed to support you about local software / programs."
    
    # Admin rights
    elif any(word in text_lower for word in ['admin', 'administrator', 'elevated', 'admin rights', 'privileges']):
        return "admin_rights", "Need: Extra information needed to request admin rights on the computer."
    
    # Employee offboarding
    elif any(word in text_lower for word in ['offboard', 'leaving', 'last day', 'equipment return']):
        return "offboarding", "Need: Extra information needed to start the IT Off-boarding process."
    
    # Absence requests
    elif any(word in text_lower for word in ['absence', 'vacation', 'time off', 'successfactors']):
        return "absence_request", "Need: Extra information needed to request an Absence ticket."
    
    # Badge/access requests
    elif any(word in text_lower for word in ['badge', 'access card', 'building access', 'office access']):
        return "badge_access", "Need: Extra information needed to request office access."
    
    # Email support
    elif any(word in text_lower for word in ['email', 'mailbox', 'outlook', 'mail']):
        return "email_support", "Need: Extra information needed to support you with email/mailbox issues."
    
    # Password reset
    elif any(word in text_lower for word in ['password', 'reset', 'unlock', 'account locked']):
        return "password_reset", "Need: Extra information needed to reset your password."
    
    # Printer support
    elif any(word in text_lower for word in ['printer', 'printing', 'print']):
        return "printer_support", "Need: Extra information needed to support you with printer issues."
    
    # Hardware support
    elif any(word in text_lower for word in ['hardware', 'laptop', 'desktop', 'monitor', 'keyboard', 'mouse']):
        return "hardware_support", "Need: Extra information needed to support you with hardware issues."
    
    else:
        return "other", "Thank you for your request. I will review the details and get back to you shortly."


# Resolution Service class
class ResolutionService:
    def __init__(self, knowledge_base_path: str, ticket_classifier_path: str, team_classifier_path: str):
        """Initialize the resolution service with models and RAG system"""
        self.knowledge_base_path = knowledge_base_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load ticket classifier (classifies tickets into categories)
        self.ticket_classifier = None
        self.ticket_tokenizer = None
        self.ticket_label_encoder = None
        self._get_ticket_classifier(ticket_classifier_path)

        # Team classifier (lazy loaded)
        self.team_classifier = None
        self.team_tokenizer = None
        self.team_label_encoder = None
        self.team_classifier_path = team_classifier_path
        
        # RAG cache will be initialized on first request
        self._rag_cache = {"kb_path": None, "kb_mtime": None, "rag": None, "df": None}
    
    def classify_team_with_distilbert(self, ticket_text, service_category=None, service_subcategory=None):
        """
        Use trained DistilBERT model to predict which team should handle the ticket
        """
        
        # Lazy load the model on first use
        classifier, tokenizer, device = self._get_team_classifier()
        
        if classifier is None or tokenizer is None:
            print("⚠️ Team classifier not available, using fallback")
            return "Unknown Team", 0.0
        
        # Parse the input properly
        lines = ticket_text.split('\n', 1) if '\n' in ticket_text else ticket_text.split(' ', 1)
        title = lines[0].strip() if lines else ""
        description = lines[1].strip() if len(lines) > 1 else ticket_text.strip()
        
        # Format input EXACTLY like in the notebook training - this is critical!
        formatted_text = f"[TITLE] {title} [DESCRIPTION] {description}"
        
        # Add service information exactly as in training
        if service_category:
            formatted_text += f" [SERVICE CATEGORY] {service_category}"
        if service_subcategory:
            formatted_text += f" [SERVICE SUBCATEGORY] {service_subcategory}"
        
        print(f"📋 DistilBERT input: {formatted_text[:150]}...")
        
        try:
            # Use EXACT same tokenization parameters as training
            inputs = tokenizer(
                formatted_text, 
                return_tensors="pt", 
                truncation=True, 
                padding='max_length',  # Changed from padding=True
                max_length=512
            ).to(device)
            
            # Get prediction
            with torch.no_grad():
                outputs = classifier(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class_idx = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities.max().item()
            
            # ALWAYS use label encoder first - this is the most accurate approach
            try:
                with open(self.team_classifier_path + '/label_encoder.pkl', 'rb') as f:
                    team_label_encoder = pickle.load(f)
                predicted_team = team_label_encoder.inverse_transform([predicted_class_idx])[0]
                print(f"🎯 Predicted team: {predicted_team} (confidence: {confidence:.3f}) [Using CSV label encoder]")
            except Exception as le_error:
                print(f"⚠️ Label encoder error, using TEAM_MAPPING fallback: {le_error}")
                predicted_team = TEAM_MAPPING.get(predicted_class_idx, "(GI-SM) Service Desk")
                print(f"🎯 Predicted team: {predicted_team} (confidence: {confidence:.3f}) [Using TEAM_MAPPING fallback]")
            
            return predicted_team, confidence
            
        except Exception as e:
            print(f"❌ Error in DistilBERT team classification: {e}")
            return "(GI-SM) Service Desk", 0.5  # Default fallback


    def _get_team_classifier(self):
        """Lazy load team classifier model on first use.
        
        Returns:
            tuple: (model, tokenizer, device) or (None, None, None) if loading fails
        """
        
        if self.team_classifier is not None:
            return self.team_classifier, self.team_tokenizer, self.device
        
        try:
            #logger.info(f"Loading team classifier from {TEAM_CLASSIFIER_PATH}")
            self.team_tokenizer = DistilBertTokenizer.from_pretrained(self.team_classifier_path)
            self.team_classifier = DistilBertForSequenceClassification.from_pretrained(self.team_classifier_path)
            self.team_classifier.to(self.device)
            self.team_classifier.eval()
            
            #logger.info(f"Team classifier loaded: {_team_classifier.num_labels} labels, device: {_device}")
            
            return self.team_classifier, self.team_tokenizer, self.device
        except Exception as e:
            #logger.error(f"Error loading team classifier: {e}")
            return None, None, None


    
    def _get_ticket_classifier(self, ticket_classifier_path: str):
        """Load the ticket classification model"""
        try:
            # Load ticket classification model
            from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
            
            self.ticket_tokenizer = DistilBertTokenizer.from_pretrained(ticket_classifier_path)
            self.ticket_classifier = DistilBertForSequenceClassification.from_pretrained(ticket_classifier_path)
            self.ticket_classifier.to(self.device)
            self.ticket_classifier.eval()
            
            # Load label encoder
            with open(f'{ticket_classifier_path}/label_encoder.pkl', 'rb') as f:
                self.ticket_label_encoder = pickle.load(f)
            
            # Load metadata
            with open(f'{ticket_classifier_path}/metadata.json', 'r') as f:
                ticket_metadata = json.load(f)
            
            print(f"✅ Ticket classifier loaded successfully from {ticket_classifier_path}")
            print(f"📊 Ticket classifier classes: {ticket_metadata['classes']}")
            
        except Exception as e:
            print(f"❌ Error loading ticket classifier: {e}")
            print("💡 Falling back to keyword-based classification")
            ticket_classifier = None
    
    def _get_or_build_rag(self, force_rebuild: bool = False):
        """Return cached RAG system unless source CSV changed or rebuild forced."""
        try:
            current_mtime = os.path.getmtime(self.knowledge_base_path)
        except OSError:
            current_mtime = None
        cache_ok = (
            self._rag_cache["rag"] is not None and
            self._rag_cache["kb_path"] == self.knowledge_base_path and
            (current_mtime is None or self._rag_cache["kb_mtime"] == current_mtime) and
            not force_rebuild
        )
        if cache_ok:
            return self._rag_cache["rag"], self._rag_cache["df"]

        # (Re)build
        df = load_knowledge_base(self.knowledge_base_path)
        rag = RAGSystem(df, kb_path=self.knowledge_base_path)
        rag.build_index(kb_path=self.knowledge_base_path, kb_mtime=current_mtime)
        self._rag_cache.update({
            "kb_path": self.knowledge_base_path,
            "kb_mtime": current_mtime,
            "rag": rag,
            "df": df
        })
        return rag, df

    
    def classify_ticket(self, ticket_text: str, service_category=None, service_subcategory=None):
        """Classify ticket type (e.g., vpn_request, onboarding)"""
        # Parse the input properly
        lines = ticket_text.split('\n', 1) if '\n' in ticket_text else ticket_text.split(' ', 1)
        title = lines[0].strip() if lines else ""
        description = lines[1].strip() if len(lines) > 1 else ticket_text.strip()
        
        # Format input EXACTLY like in training
        formatted_text = f"[TITLE] {title} [DESCRIPTION] {description}"
        
        # Add service information if available
        if service_category:
            formatted_text += f" [SERVICE] {service_category}"
        if service_subcategory:
            formatted_text += f" [SUBCATEGORY] {service_subcategory}"
        
        #print(f"📋 Ticket classifier input: {formatted_text[:150]}...")
        
        # Try using the trained model first
        if self.ticket_classifier is not None and self.ticket_tokenizer is not None and self.ticket_label_encoder is not None:
            try:
                # Tokenize input
                inputs = self.ticket_tokenizer(
                    formatted_text,
                    return_tensors="pt",
                    truncation=True,
                    padding='max_length',
                    max_length=512
                ).to(self.device)
                
                # Get prediction
                with torch.no_grad():
                    outputs = self.ticket_classifier(**inputs)
                    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    predicted_class_idx = torch.argmax(probabilities, dim=-1).item()
                    confidence = probabilities.max().item()
                
                # Convert to original label
                predicted_class = self.ticket_label_encoder.inverse_transform([predicted_class_idx])[0]
                
                #print(f"🎯 Predicted ticket type: {predicted_class} (confidence: {confidence:.3f})")
                
                # Map predicted class to template response
                template_response = get_template_response_for_class(predicted_class)
                
                return predicted_class, template_response
                
            except Exception as e:
                print(f"❌ Error in model-based classification: {e}")
                print("💡 Falling back to keyword-based classification")
        
        # Fallback to keyword-based classification
        return classify_ticket_with_keywords(ticket_text, service_category, service_subcategory)

    
    def generate_response_with_openai(self, ticket_title, ticket_description, 
                                     classification, predicted_team, team_confidence,
                                     similar_replies, temporal_context='standard'):
        """
        Main response generation orchestrator
        Enhanced response generation with simple template vs personalized detection
        """
        # Analyze similar replies to determine response type
        template_examples = []
        personalized_examples = []
        
        print(f"🔍 Analyzing {len(similar_replies)} similar replies...")
        
        for _, reply in similar_replies.iterrows():
            first_reply = str(reply.get('first_reply', ''))
            response_type, confidence = analyze_response_type_simple(first_reply)
            
            print(f"   Reply: {response_type} (confidence: {confidence:.2f})")
            
            if response_type == "template" and confidence > 0.5:
                template_examples.append(reply)
            elif response_type == "personalized" and confidence > 0.5:
                personalized_examples.append(reply)
        
        # Decide which approach to use
        use_template = len(template_examples) > len(personalized_examples)

        # If temporal/status-update context is detected, prefer personalized status-update responses
        if temporal_context == 'temporal_update':
            print("🔔 Temporal context detected — forcing personalized/status-update response")
            use_template = False

        print(f"📊 Decision: {'Template' if use_template else 'Personalized'}")
        print(f"   Template examples: {len(template_examples)}")
        print(f"   Personalized examples: {len(personalized_examples)}")
        
        # Generate appropriate response using existing functions
        if use_template and template_examples:
            print("🔧 Generating template response...")
            # Convert list of Series to DataFrame for template function
            if isinstance(template_examples[0], pd.Series):
                template_df = pd.DataFrame(template_examples)
            else:
                template_df = pd.DataFrame(template_examples)
            return self.generate_template_response_function(ticket_title, ticket_description, classification, predicted_team, template_df)
        else:
            print("💬 Generating personalized response...")
            # Convert list of Series to DataFrame or use original similar_replies
            if personalized_examples:
                if isinstance(personalized_examples[0], pd.Series):
                    personalized_df = pd.DataFrame(personalized_examples)
                else:
                    personalized_df = pd.DataFrame(personalized_examples)
            else:
                personalized_df = similar_replies  # Use original DataFrame
            
            # If temporal/context is status update, use dedicated status-update generator
            if temporal_context == 'temporal_update':
                return self.generate_status_update_response(ticket_title, ticket_description, classification, predicted_team, team_confidence, personalized_df)

            return self.generate_response_with_openai_personal(ticket_title, ticket_description, classification, predicted_team, team_confidence, personalized_df)
        
    def generate_template_response_function(self, ticket_title, ticket_description, 
                                   classification, predicted_team, template_examples):
        """Generate template-based response with enhanced similarity matching"""
        
        # Ensure template_examples is a DataFrame
        if isinstance(template_examples, list):
            template_examples = pd.DataFrame(template_examples)
        
        # Enhanced template selection - find the MOST similar template
        if len(template_examples) > 1:
            template_examples = select_best_templates(ticket_title, ticket_description, template_examples, top_k=3)
        
        # Create more specific prompts based on ticket type
        specific_instructions = get_specific_instructions(classification, predicted_team)
        
        prompt = (
            f"You are an IT support system that generates STRUCTURED TEMPLATE RESPONSES. "
            f"You must follow the EXACT format and structure shown in the examples below.\n\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"- Copy the EXACT format from the most similar ticket\n"
            f"- Use IDENTICAL structure, field names, and formatting\n"
            f"- Replace ONLY the specific values (names, IDs, etc.)\n"
            f"- Keep ALL punctuation, spacing, and line breaks\n"
            f"- Start with 'Below you will find' when appropriate\n"
            f"- Use bullet points (-) exactly as shown\n"
            f"{specific_instructions}\n\n"
            f"Current Ticket:\n"
            f"Title: {ticket_title}\n"
            f"Description: {ticket_description}\n"
            f"Request Type: {classification}\n"
            f"Assigned Team: {predicted_team}\n\n"
            f"TEMPLATE EXAMPLES (RANKED BY SIMILARITY):\n"
        )
        
        # Add template examples with enhanced context
        example_count = 0
        for index, reply in template_examples.iterrows():
            if example_count >= 2:  # Reduced to 2 best examples for focus
                break
                
            similarity_note = f"[SIMILARITY: {reply.get('enhanced_score', 0.0):.3f}]" if 'enhanced_score' in reply else ""
            prompt += (
                f"EXAMPLE {example_count + 1} {similarity_note}:\n"
                f"Title: {reply.get('Title_anon', 'N/A')}\n"
                f"Description: {reply.get('Description_anon', 'N/A')[:200]}...\n"
                f"EXACT TEMPLATE TO FOLLOW:\n{reply.get('first_reply', 'N/A')}\n"
                f"{'='*60}\n\n"
            )
            example_count += 1
        
        prompt += (
            f"GENERATE RESPONSE:\n"
            f"Use the EXACT structure from the most similar example above. "
            f"Copy the format precisely - same field names, same punctuation, same layout. "
            f"Change ONLY the specific details relevant to the current ticket. "
            f"Do NOT add extra text or modify the template structure."
        )

        #print("Prompt sent to OpenAI API (Enhanced Template):")
        #print(prompt[:800] + "..." if len(prompt) > 800 else prompt)

        try:
            return _chat_completion(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an IT support system that generates responses matching the exact format and style of provided examples."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2,
                top_p=0.8,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Sorry, we encountered an issue generating a response. Please try again later."

    
    def generate_personalized_response(self, ticket_title, ticket_description,
                                       classification, predicted_team, team_confidence,
                                       similar_replies):
        """Enhanced personalized response generation with better context awareness"""
        
        # Enhanced context analysis
        context_analysis = analyze_ticket_context(ticket_title, ticket_description, classification)
        
        # Select best similar replies
        if len(similar_replies) > 2:
            similar_replies = select_best_similar_replies(ticket_title, ticket_description, similar_replies, top_k=2)
        
        # Construct enhanced prompt
        prompt = (
            f"You are an expert IT support specialist generating a professional first reply. "
            f"Use the context and similar examples to create a response that matches the expected format and tone.\n\n"
            f"CURRENT TICKET:\n"
            f"Title: {ticket_title}\n"
            f"Description: {ticket_description}\n"
            f"Request Type: {classification}\n"
            f"Assigned Team: {predicted_team} (confidence: {team_confidence:.2f})\n"
            f"Context: {context_analysis}\n\n"
            f"SIMILAR RESOLVED TICKETS FOR REFERENCE:\n"
        )
        
        # Add similar replies with better formatting
        for i, (_, reply) in enumerate(similar_replies.iterrows(), 1):
            prompt += (
                f"{i}. Similar Ticket Title: {reply['Title_anon']}\n"
                f"   Similar Ticket Description: {reply['Description_anon'][:300]}...\n"
                f"   First Reply: {reply['first_reply']}\n\n"
            )
        
        # Enhanced instructions based on patterns
        response_style = determine_response_style(similar_replies)
        
        prompt += (
            f"RESPONSE REQUIREMENTS:\n"
            f"- Style: {response_style}\n"
            f"- Match the tone and structure of similar replies\n"
            f"- Address the specific request clearly and professionally\n"
            f"- Include relevant next steps or requirements\n"
            f"- Keep length appropriate for first reply (150-300 words)\n\n"
            f"Generate a professional first reply that follows the patterns shown in the similar tickets above:"
        )

        print("Prompt sent to OpenAI API (Enhanced Personal):")
        print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)

        # Call OpenAI API with optimized parameters
        try:
            return _chat_completion(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert IT support specialist who writes clear, professional responses that match organizational standards."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3,
                top_p=0.8,
                frequency_penalty=0.1,
                presence_penalty=0.2
            )
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Sorry, we encountered an issue generating a response. Please try again later."

    
    def generate_status_update_response(self, ticket_title, ticket_description,
                                        classification, predicted_team, team_confidence,
                                        similar_replies):
        """Generate a structured status-update style first reply for incidents/outages/recovery messages.

        This aims to mirror the organization's past global communications (e.g., "Yesterday, from Group IT...") and
        include: current status, impact, known workarounds, next steps, and contact/ETA where available.
        """
        # Build concise context from similar replies
        examples_text = ""
        for i, (_, r) in enumerate(similar_replies.head(3).iterrows(), 1):
            fr = r.get('first_reply', '')
            examples_text += f"{i}. {str(fr)[:400].strip()}\n\n"

        prompt = (
            "You are an IT operations communicator. Produce a clear STATUS UPDATE first reply for users reporting an ongoing "
            "system issue. Follow this structure EXACTLY:\n\n"
            "- Short subject line starting with 'Status Update:'\n"
            "- Opening paragraph acknowledging the incident and sourcing the communication (e.g., 'Yesterday, from Group IT')\n"
            "- Current status (what we know)\n"
            "- Impacted services / example identifiers (invoices, systems)\n"
            "- Known workarounds or temporary steps (if any)\n"
            "- Next steps & ETA (if available) and contact for urgent issues\n"
            "- Short closing\n\n"
            f"TICKET:\nTitle: {ticket_title}\nDescription: {ticket_description}\nAssigned Team: {predicted_team} (confidence: {team_confidence:.2f})\n\n"
            f"SIMILAR_EXAMPLES:\n{examples_text}\n\n"
            "Generate the STATUS UPDATE now. Keep it factual, short paragraphs, 120-220 words. If you don't have ETA, say 'investigating' and provide workarounds if present."
        )

        print("Prompt sent to OpenAI API (Status Update):")
        print(prompt[:800] + '...' if len(prompt) > 800 else prompt)

        try:
            return _chat_completion(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an IT operations communicator writing concise status updates."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.2,
                top_p=0.8
            )
        except Exception as e:
            print(f"Error calling OpenAI API for status update: {e}")
            return (
                "Subject: Status Update - we are investigating an issue\n\n"
                "Dear user,\n\nWe acknowledge the reported issue and are currently investigating. Our team will provide an update as soon as more information is available. "
                "If you have urgent business impact, please reply with 'URGENT' and include examples/IDs.\n\nRegards,\nIT Operations"
            )

    def generate_response(self, ticket_title, ticket_description, rag_system, retrieval_k: int = 5):
        """
        Enhanced response generation with improved retrieval
        """
        ticket_text = ticket_title + " " + ticket_description
        word_class, template = self.classify_ticket(ticket_text)

        # Map word_class to category labels for filtering
        category_mapping = {
            "vpn_request": "to enable Client-to-Site VPN tunnel requests",
            "onboarding": "to start the IT On-boarding of a new internal employee",
            "software_request": "to request a software or a licence on my Windows device",
            "offboarding": "to start the IT Off-boarding process",
            "absence_request": "to request an Absence ticket",
            "admin_rights": "to request admin rights on the computer"
        }
        
        predicted_category = category_mapping.get(word_class, None)
        predicted_team, team_confidence = self.classify_team_with_distilbert(ticket_text)

        # Detect temporal/status-update context and pass to generator
        temporal_context = detect_temporal_context(ticket_title, ticket_description)

        # Use enhanced retrieval with category awareness
        similar_replies = rag_system.retrieve_similar_replies(
            ticket_text,
            top_k=retrieval_k,
            predicted_category=predicted_category
        )

        # Generate response with better context
        response = self.generate_response_with_openai(ticket_title, ticket_description, word_class, predicted_team, team_confidence, similar_replies, temporal_context=temporal_context)

        return {
            "classification": word_class,
            "predicted_team": predicted_team,
            "team_confidence": team_confidence,
            "response": response,
            "similar_replies": similar_replies.to_dict(orient="records"),
            "predicted_class": word_class,
            "retrieval_k": retrieval_k
        }
    
    
    def rebuild_embeddings(self):
        """Force a fresh embedding build ignoring any existing cache.

        Returns a summary dict with basic stats. This sets DISABLE_EMBEDDING_CACHE=1
        temporarily so that the RAGSystem.build_index path always recomputes
        embeddings instead of loading a cached .npz. After building we manually
        persist a new cache file so subsequent standard calls can load it fast.
        """
        prev_disable = os.environ.get("DISABLE_EMBEDDING_CACHE")
        os.environ["DISABLE_EMBEDDING_CACHE"] = "1"
        try:
            # Force rebuild by passing force_rebuild=True
            rag, df = self._get_or_build_rag(self.knowledge_base_path, force_rebuild=True)
            records = len(df)
            emb_dim = int(rag.embeddings.shape[1]) if rag.embeddings is not None else None

            # Manually save a fresh cache (mirrors logic in build_index)
            cache_file = None
            saved_cache = False
            try:
                if rag.kb_path and rag.embeddings is not None:
                    kb_mtime = os.path.getmtime(rag.kb_path)
                    safe_model = rag.sentence_model_name.replace('/', '_')
                    cache_key = f"{os.path.basename(rag.kb_path)}_{safe_model}_{int(kb_mtime)}"
                    cache_dir = "embeddings_cache"
                    os.makedirs(cache_dir, exist_ok=True)
                    cache_file = os.path.join(cache_dir, f"{cache_key}.npz")
                    np.savez_compressed(
                        cache_file,
                        title_embeddings=rag.title_embeddings,
                        description_embeddings=rag.description_embeddings,
                        embeddings=rag.embeddings,
                    )
                    saved_cache = True
            except Exception as e:
                print(f"⚠️ Failed to persist rebuilt embeddings cache: {e}")

            return {
                "rebuilt": True,
                "records": records,
                "embedding_dim": emb_dim,
                "cache_file": cache_file,
                "cache_saved": saved_cache,
            }
        finally:
            # Restore prior setting
            if prev_disable is None:
                os.environ.pop("DISABLE_EMBEDDING_CACHE", None)
            else:
                os.environ["DISABLE_EMBEDDING_CACHE"] = prev_disable

    
    def _fallback_response(self, ticket_title, ticket_description, classification, predicted_team, similar_replies_df):
        """Offline fallback if OpenAI unavailable or errors occur."""
        snippet = ""
        if similar_replies_df is not None and not similar_replies_df.empty:
            first = similar_replies_df.iloc[0]
            snippet = (str(first.get('first_reply', '')) or '')[:400]
        return (
            f"[Fallback Generated Reply]\n"
            f"Request Type: {classification}\nPredicted Team: {predicted_team}\n"
            f"We received your ticket titled '{ticket_title}'. We are reviewing the details and will proceed accordingly."
            + (f"\n\nReference example (trimmed):\n{snippet}" if snippet else "")
        )

    def save_resolved_ticket_with_feedback(
        self,
        ticket_title: str,
        ticket_description: str,
        edited_response: str,
        predicted_team: str = None,
        predicted_classification: str = None,
        service_name: str = None,
        service_subcategory: str = None
    ):
        """
        Save resolved ticket with user feedback for incremental learning.
        
        INCREMENTAL UPDATE: Adds single embedding to FAISS without full rebuild.
        
        Returns:
            dict: {success, message, ticket_ref, new_kb_size, embedding_added_incrementally}
        """
        import datetime
        import numpy as np
        import faiss
        
        try:
            # Auto-classify if not provided
            if predicted_team is None or predicted_classification is None:
                print("🔄 Auto-classifying ticket...")
                ticket_text = f"{ticket_title} {ticket_description}"
                
                if predicted_classification is None:
                    predicted_classification, _ = self.classify_ticket(
                        ticket_text,
                        service_category=service_name,
                        service_subcategory=service_subcategory
                    )
                    print(f"📊 Auto-classified: {predicted_classification}")
                
                if predicted_team is None:
                    predicted_team = "Unknown Team"  # TODO: Use your team classifier
            
            # Use cached knowledge base if available
            if self._rag_cache.get("df") is not None:
                df = self._rag_cache["df"].copy()
                print(f"📊 Using cached KB: {len(df)} tickets")
            else:
                df = pd.read_csv(self.knowledge_base_path)
                print(f"📊 Loaded KB from disk: {len(df)} tickets")
            
            # Generate unique ticket reference
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ticket_ref = f"FEEDBACK_{timestamp}"
            
            # Format as Public_log_anon
            formatted_public_log = (
                f"********** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} **********\n"
                f": servicedesk (0) **********\n"
                f"{edited_response}\n"
            )
            
            # Create new row
            new_row = {
                'Ticket_Reference': ticket_ref,
                'Title_anon': ticket_title,
                'Description_anon': ticket_description,
                'Public_log_anon': formatted_public_log,
                'first_reply': edited_response,
                'label_auto': predicted_classification,
                'Team': predicted_team,
                'Service_Name': service_name or 'Unknown',
                'Service_Subcategory': service_subcategory or 'Unknown',
                'Status': 'Resolved',
                'Priority': 'Normal',
                'Source': 'API_Feedback'
            }
            
            # Add missing columns
            for col in df.columns:
                if col not in new_row:
                    new_row[col] = None
            
            # Append to dataframe
            new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to CSV
            new_df.to_csv(self.knowledge_base_path, index=False)
            
            # INCREMENTAL EMBEDDING UPDATE
            embedding_added = False
            
            if self._rag_cache.get("rag") is not None:
                try:
                    print(f"⚡ Adding single embedding (incremental)...")
                    rag_system = self._rag_cache["rag"]
                    
                    old_index_size = rag_system.index.ntotal
                    old_kb_size = len(rag_system.knowledge_base)
                    
                    # Generate embeddings for new ticket
                    new_text = f"{ticket_title} {ticket_description}".strip()
                    new_combined_emb = rag_system.sentence_model.encode([new_text], convert_to_numpy=True)
                    new_combined_emb = np.array(new_combined_emb, dtype='float32')
                    faiss.normalize_L2(new_combined_emb)
                    
                    new_title_emb = rag_system.sentence_model.encode([ticket_title], convert_to_numpy=True)
                    new_title_emb = np.array(new_title_emb, dtype='float32')
                    
                    new_desc_emb = rag_system.sentence_model.encode([ticket_description], convert_to_numpy=True)
                    new_desc_emb = np.array(new_desc_emb, dtype='float32')
                    
                    # Add to FAISS index
                    rag_system.index.add(new_combined_emb)
                    
                    # Update embedding arrays
                    if rag_system.embeddings is not None:
                        rag_system.embeddings = np.vstack([rag_system.embeddings, new_combined_emb])
                        rag_system.title_embeddings = np.vstack([rag_system.title_embeddings, new_title_emb])
                        rag_system.description_embeddings = np.vstack([rag_system.description_embeddings, new_desc_emb])
                    
                    # Update knowledge base
                    rag_system.knowledge_base = new_df.copy()
                    
                    # Rebuild category index
                    rag_system._build_category_index()
                    
                    # Update cache
                    self._rag_cache["df"] = new_df
                    self._rag_cache["kb_mtime"] = os.path.getmtime(self.knowledge_base_path)
                    self._rag_cache["rag"] = rag_system
                    
                    # Verify
                    if rag_system.index.ntotal == old_index_size + 1:
                        embedding_added = True
                        print(f"✅ Verification passed! New ticket available!")
                    else:
                        raise Exception("Incremental update verification failed")
                    
                except Exception as e:
                    print(f"⚠️ Incremental embedding failed: {e}")
                    print(f"🔄 Cache invalidated - rebuild on next request")
                    self._rag_cache = {"kb_path": None, "kb_mtime": None, "rag": None, "df": None}
            else:
                print(f"💡 No active RAG - embedding on next request")
            
            return {
                "success": True,
                "message": "Ticket feedback saved (incremental)" if embedding_added else "Ticket feedback saved",
                "ticket_ref": ticket_ref,
                "new_kb_size": len(new_df),
                "embedding_added_incrementally": embedding_added,
                "embedding_invalidated": not embedding_added
            }
            
        except Exception as e:
            print(f"❌ Error saving feedback: {e}")
            return {
                "success": False,
                "message": f"Failed: {str(e)}",
                "ticket_ref": None,
                "new_kb_size": None,
                "embedding_invalidated": False
            }

    # Main function to process a new ticket (now cached)
    def process_new_ticket(self, request: ResolutionRequest):
        rag_system, df = self._get_or_build_rag(force_rebuild=request.force_rebuild)
        result = self.generate_response(request.ticket_title, request.ticket_description, rag_system, retrieval_k=request.top_k)

        # NO FALLBACK - Let any errors propagate so we can see what's wrong
        return result