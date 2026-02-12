# HumAL - Presentation Guide

## What is HumAL?

**HumAL** (HumAIne Active Learning) is a full-stack platform that enables **human-in-the-loop machine learning** for IT service management. It combines traditional ML, Large Language Models (LLMs), and explainable AI to automate ticket classification and resolution generation.

---

## The Problem We Solve

| Challenge | Impact |
|-----------|--------|
| IT support teams are overwhelmed with ticket volume | Slow response times, frustrated users |
| Manual ticket routing causes delays | Tickets go to wrong teams, bouncing around |
| Training ML models requires massive labeled datasets | Expensive, time-consuming data labeling |
| AI predictions feel like "black boxes" | Low trust, reluctance to adopt |

**HumAL addresses all of these with a human-centered AI approach.**

---

## Key Features to Highlight

### 1. Active Learning Pipeline
- **Smart sample selection** - The system picks the most informative tickets for humans to label
- **Iterative training** - Model improves after every labeling batch
- **Reduced labeling effort** - Achieve high accuracy with fewer labeled examples
- **Multiple strategies**: Uncertainty, Margin, Entropy, Random sampling

### 2. Automated Ticket Classification
- Route tickets to the correct support team automatically
- Choose from multiple ML models:
  - Logistic Regression, Random Forest, SVM, Gradient Boosting, Neural Network
- Real-time predictions with confidence scores

### 3. RAG-Powered Resolution Generation
- Uses **Retrieval-Augmented Generation** (RAG) with OpenAI GPT
- Finds similar past tickets from a knowledge base
- Generates contextual first-reply responses
- Speeds up agent response time significantly

### 4. Explainable AI (XAI)
- **LIME explanations** show which words influenced the prediction
- **Similar ticket retrieval** provides context for decisions
- Builds trust and allows humans to verify AI recommendations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│              Vue.js / TypeScript / Tailwind                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│                        Backend                               │
│                   FastAPI (Python)                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Active       │ Inference    │ Resolution   │ XAI            │
│ Learning     │ Service      │ (RAG)        │ (LIME)         │
│ Service      │              │              │                │
├──────────────┴──────────────┴──────────────┴────────────────┤
│          scikit-learn │ PyTorch │ FAISS │ OpenAI           │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Vue 3, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI, Python 3.8+ |
| **ML/NLP** | scikit-learn, PyTorch, Sentence Transformers |
| **Vector Search** | FAISS (for similarity search) |
| **LLM** | OpenAI GPT (for resolution generation) |
| **XAI** | LIME (Local Interpretable Model-agnostic Explanations) |

---

## Demo Walkthrough

### Page 1: Training
- Create a new Active Learning instance
- Select model type and query strategy
- Watch accuracy metrics improve over iterations

### Page 2: Dispatch Labeling
- Human-in-the-loop labeling interface
- View model predictions + LIME explanations
- Assign correct team labels
- Model automatically retrains after each batch

### Page 3: Inference
- Input new ticket details
- Get instant team prediction with confidence
- See LIME explanation and similar tickets

### Page 4: Ticket Resolution
- Enter ticket information
- Generate AI-powered resolution using RAG
- Review similar past tickets and their solutions

---

## Key Metrics & Value Proposition

- **Reduced labeling effort**: Active learning typically needs 30-50% fewer labels than random sampling
- **Faster ticket routing**: Automated classification in milliseconds
- **Improved response time**: AI-generated resolutions as first drafts
- **Transparency**: Every prediction comes with an explanation

---

## Future Directions

- Multi-language support
- Integration with ITSM tools (ServiceNow, Jira Service Management)
- Continuous learning from production feedback
- Custom model fine-tuning

---

## Questions to Prepare For

1. **How does active learning reduce labeling costs?**
   - By strategically selecting uncertain samples, we maximize information gain per label

2. **Why use LIME for explainability?**
   - Model-agnostic, works with any classifier, provides intuitive word-level explanations

3. **How does the RAG system work?**
   - Embeds tickets with Sentence Transformers, uses FAISS for similarity search, feeds context to GPT

4. **What about data privacy with OpenAI?**
   - Only ticket text is sent; can be configured for on-premise LLMs if needed

---

## Running the Demo

```bash
# Start both frontend and backend
.\start-dev.bat   # Windows
./start-dev.sh    # Linux/Mac

# Access points
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```
