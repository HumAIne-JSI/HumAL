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
- Sample data loaded in `backend/data/`

### First Time Setup
1. Ensure the backend and frontend are running
2. Navigate to `http://localhost:5173` in your browser
3. You should see the HumAL landing page

---

## Application Overview

HumAL consists of five main pages:

1. **Home** - Landing page and navigation hub
2. **Training** - Create and configure active learning instances
3. **Dispatch Labeling** - Label tickets for team routing
4. **Ticket Resolution** - Generate automated ticket responses
5. **Inference** - Run predictions on new tickets

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

### 2. Training Page (`/training`)

**Purpose**: Create and manage active learning instances for model training.

#### Creating a New Instance

**Step 1: Configure Instance**

1. **Model Selection**
   - Choose from available models:
     - **Logistic Regression**: Fast, interpretable, good for text classification
     - **Random Forest**: Robust, handles non-linear patterns
     - **SVM**: Effective for high-dimensional data
     - **Gradient Boosting**: High accuracy, slower training
     - **Neural Network**: Best for large datasets

2. **Query Strategy**
   - **Uncertainty Sampling**: Selects samples the model is most uncertain about (recommended)
   - **Margin Sampling**: Selects samples with smallest margin between top predictions
   - **Entropy Sampling**: Selects samples with highest prediction entropy
   - **Random Sampling**: Random selection (baseline)

**Step 2: Create Instance**

Click "Create Active Learning Instance" button. You'll receive an instance ID (e.g., Instance #1).

---

### 3. Dispatch Labeling Page (`/dispatch-labeling`)

**Purpose**: Interactive interface for labeling tickets with team assignments.

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
- **Current Prediction**: Model's current guess (if available)
- **LIME explanations**: Keywords and their importances
- **Similar Ticket**: The most similar ticket

**Step 4: Assign Labels**

1. Read the ticket description, model prediction and LIME explanations
2. Select the appropriate team from the dropdown

**Step 5: Submit Labels**

1. System automatically:
   - Saves your labels
   - Retrains the model with new data
   - Updates accuracy metrics
   - Prepares next batch

**Step 8: Iterate**

Repeat steps 2-6 until:
- Accuracy reaches your target (e.g., 90%)
- Unlabeled pool is exhausted
- Model performance plateaus

---

### 4. Ticket Resolution Page (`/resolution-labeling`)

**Purpose**: Generate automated first-reply responses for IT support tickets using an LLM.

#### How It Works

The system uses **Retrieval-Augmented Generation (RAG)**:
1. Finds similar tickets from knowledge base
2. Retrieves their resolutions
3. Uses GPT to generate contextually appropriate response

#### Using the Resolution Generator

**Step 1: Enter Ticket Information**

1. Ticket Category
2. Ticket Subcategory
3. Ticket Title
4. Ticket Description

**Step 2: Generate Resolution**

Click "Generate Resolution" button.

**Step 3: Review Generated Response**

The system displays:

1. **Generated Resolution**

2. **Similar Tickets**
   - Top 3 similar past tickets
   - Their resolutions
   - Similarity scores
   - Useful for verification

**Step 4: Evaluate and Edit**

1. Read the generated resolution carefully
2. Check for:
   - Technical accuracy
   - Completeness
   - Appropriate tone
   - Relevant troubleshooting steps
3. Edit if necessary before sending to user

---

### 5. Inference Page (`/inference`)

**Purpose**: Run predictions on new, unlabeled tickets using trained models.

#### Prerequisites

- At least one trained active learning instance
- Test tickets ready for classification

#### Running Inference

**Step 1: Select Model**

1. Choose active learning instance from dropdown
2. System loads the latest trained model

**Step 2: Input Tickets**

1. Select the ticket category
2. Select the ticket subcategory
3. Input  the tickt title
4. Input the ticket description

**Step 3: Run Prediction**


**Step 4: Review Results**

The system shows:

1. **Predicted Team**
   - Most likely team assignment
   - Color-coded by confidence

2. **LIME Explanation**
   - Visual representation
   - Highlighted key terms
   - Weight of each feature

3. **Similar Training Example**
   - Ticket the most similar to the current one
   - Similarity score