# HumAL User Guide

## Introduction

Welcome to HumAL, an integrated platform for training machine learning models with human feedback.

This guide will help you understand and use all features of the platform effectively.

---

## Getting Started

### Prerequisites
- HumAL installed and running (see [README.md](../README.md) for installation)
- Backend API running at `http://localhost:8000`
- Frontend application running at `http://localhost:5173`
- Data loaded in `backend/data/`
---

## Application Overview

HumAL consists of five main pages:

1. **Home** - Landing page and navigation hub
2. **New Project** - Create and configure active learning instances
3. **Assign Manually** - Label tickets for team routing without AI assistance
4. **Smart Assign** - Label tickets with AI-powered suggestions
5. **Specialist Resolution Workspace** - Generate automated ticket responses
6. **Performance** - Analytics and model performance metrics

---

## Page-by-Page Guide

### 1. Home Page (`/`)

**Purpose**: Landing page with overview of platform features and navigation.

**Features**:
- Overview of active learning capabilities
- Quick navigation to all features

**Getting Started**:
- Click on any feature card to navigate to that section
- Use the navigation menu for quick access

---

### 2. New Project Page (`/training`)

**Purpose**: Create and manage active learning instances for model training.

#### Creating a New Instance

**Step 1: Configure Instance**

1. **Model Selection**
   - Choose from available models:
     - Logistic Regression
     - Random Forest
     - SVM

2. **Query Strategy**
- **Uncertainty Sampling Least Confidence**: Select instances with lowest confidence
- **Uncertainty Sampling Margin Sampling**: Select instances with smallest margin between top-2 classes
- **Uncertainty Sampling Entropy**: Select instances with highest prediction entropy
- **Random Sampling**: Baseline random selection
- **Query by Committee**: Ensemble disagreement

**Step 2: Create Instance**

Click "Create Active Learning Instance" button. You'll receive an instance ID.

---

### 3. Assign Manually Page (`/manual`)

**Purpose**: Label tickets for team routing without AI assistance (baseline).

#### Workflow

**Step 1: Select Active Learning Instance**
- Choose an existing instance from the dropdown

**Step 2: Load Next Ticket**
- Click "Get Next Ticket" button
- System uses query strategy to select the most informative ticket
- Tickets are displayed with their descriptions

**Step 3: Review Tickets**

Each ticket card shows:
- **Description**: Full ticket text
- **Reference**: Ticket ID for tracking
- **Metadata**: Ticket information

**Step 4: Assign Labels**

1. Read the ticket description carefully
2. Select the appropriate team from the dropdown

**Step 5: Submit Labels**

1. System automatically:
   - Saves your labels
   - Prepares next ticket
   - Tracks your labeling decisions

**Step 6: Iterate**

Repeat steps 2-5 until:
- You've labeled the desired number of tickets
- Session ends

---

### 4. Smart Assign Page (`/queue`)

**Purpose**: Label tickets for team routing with AI-powered suggestions.

#### How It Works

The system uses an active learning model to:
1. Rank tickets by uncertainty or informativeness
2. Suggest team assignments with explanations
3. Show similar previously-labeled tickets for context

#### Using Smart Assign

**Step 1: Select Active Learning Instance**
- Choose an existing instance from the dropdown

**Step 2: Load Next Ticket**
- System selects the most informative ticket using your trained model
- Displays model's top team suggestions with confidence scores

**Step 3: Review AI Suggestions**

The system displays:

1. **Top Predictions**
   - Ranked team suggestions
   - Confidence percentages

2. **LIME Explanation**
   - Visual representation of which ticket keywords influenced the suggestion
   - Highlighted key terms supporting/opposing the prediction

3. **Similar Tickets**
   - Most similar previously-labeled tickets
   - Their assigned teams for reference

**Step 4: Make a Decision**

1. **Accept** the AI suggestion (Confirm button)
2. **Override** if you disagree (Reassign button)
3. **Skip** if unsure (I Don't Know)

**Step 5: Iterate**

Repeat steps 2-4 until:
- You've labeled the desired number of tickets
- Session ends

---

### 5. Specialist Resolution Workspace Page (`/ticket-resolution`)

**Purpose**: Generate automated first-reply responses for IT support tickets using retrieval-augmented generation (RAG).

#### How It Works

The system uses **Retrieval-Augmented Generation**:
1. Finds similar past tickets from the knowledge base
2. Retrieves their resolutions
3. Uses an LLM to generate contextually appropriate response based on similar tickets

#### Using the Resolution Workspace

**Step 1: Enter Ticket Information**

1. **Ticket Title**: Enter the customer's issue title
2. **Ticket Description**: Enter the full issue description
3. **Service Category** (optional): Classify the type of issue
4. **Service Subcategory** (optional): Further specify the issue type

**Step 2: Generate Resolution**

Click "Generate solution" button. The system will:
- Optionally predict the team assignment using a trained AI model
- Retrieve similar past tickets
- Generate a suggested response

**Step 3: Review Generated Response**

The system displays:

1. **Predicted Team Assignment**
   - Suggested team for this ticket
   - Confidence percentage

2. **Suggested First Reply**
   - AI-generated response based on similar tickets
   - Editable textarea for refinements

3. **Similar Historical Tickets**
   - Top matching past tickets and their resolutions
   - Similarity scores with each ticket
   - Vote on whether suggestions are helpful

**Step 4: Evaluate and Refine**

1. Edit the suggested response as needed
2. Review similar tickets for context
3. Verify the predicted team assignment

**Step 5: Use the Response**

1. **Copy to Clipboard**: Copy the refined response for pasting
2. **Save to Knowledge Base**: Save the ticket and response for future reference
3. **Reassign Team**: Change the team assignment if needed

---

### 6. Performance Page (`/analytics`)