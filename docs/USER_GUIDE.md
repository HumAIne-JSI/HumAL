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
2. **Training** - Create and configure active learning instances
3. **Dispatch Labeling** - Label tickets for team routing
4. **Inference** - Run predictions on new tickets

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

### 3. Dispatch Labeling Page (`/dispatch-labeling`)

**Purpose**: Interactive interface for labeling tickets with dispatch teams.

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
- Accuracy reaches your target
- Unlabeled pool is exhausted
- Model performance plateaus

---

### 4. Inference Page (`/inference`)

**Purpose**: Run predictions on new, unlabeled tickets using trained models.

#### Prerequisites

- At least one trained active learning instance

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

2. **LIME Explanation**
   - Visual representation
   - Highlighted key terms
   - Weight of each feature

3. **Similar Training Example**
   - Ticket the most similar to the current one
   - Similarity score