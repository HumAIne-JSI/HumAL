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

Choosing a team and saving it are separate steps:

1. **Select** a team: the model's top suggestion is pre-selected. Pick another suggestion (keys <kbd>1</kbd>–<kbd>2</kbd>) or search any team under **Another team** (<kbd>/</kbd>) to override the model. <kbd>Esc</kbd> undoes a changed selection.
2. **Assign** (<kbd>Enter</kbd>) saves the selected team as the label and moves to the next ticket. The summary next to the button names the team and whether it is a suggestion or an override.
3. Optionally flag the label with **Tired** or **Difficult** before assigning, or **Skip — I don't know** if unsure.

The Manual Queue uses the same decision area without suggestions: search for a team, then **Assign**.

Assignments show as labeled only after saving succeeds. If saving fails, the selected team remains available to retry. Holding Enter does not assign successive tickets.

**Step 5: Iterate**

Repeat steps 2-4 until:
- You've labeled the desired number of tickets
- Session ends

---

### 5. Specialist Resolution Workspace Page (`/ticket-resolution`)

**Purpose**: Generate automated first-reply responses for IT support tickets using retrieval-augmented generation (RAG).

#### Opening the Workspace

The workspace behaves like a separate Tier 2 app. Open it from the **Specialist Resolution Workspace** link in the main sidebar (it opens in a new tab) or go to `/ticket-resolution` directly.

- **Demo sign-in**: The workspace has its own sign-in page. Enter any username and password; no real authentication takes place, and it is independent of the main app login. The sign-in lasts for the current browser tab, and **Sign out** in the sidebar footer ends it.
- **Tier 2 navigation**: The sidebar shows only the Tier 2 pages: **Specialist Resolution Workspace** and **Performance** (`/ticket-resolution/performance`, the same dashboard as the main Performance page). The project selector and the Level 1 pages are not shown.

#### How It Works

The system uses **Retrieval-Augmented Generation**:
1. Finds similar past tickets from the knowledge base
2. Retrieves their resolutions
3. Uses an LLM to generate contextually appropriate response based on similar tickets

#### Using the Resolution Workspace

The page guides you through three steps, shown as a progress indicator in the header: **Ticket → Review draft → Send to team**. Steps you can move to are clickable, for example **Ticket** to go back to step 1 from the draft; your draft is kept, and **Review draft** returns to it. The steps are locked while a reply is being generated or saved.

**Step 1: Choose a ticket**

Pick where the ticket comes from with the two tabs:

- **From queue**: Lists tickets you labeled on the Smart Assign page. Search by ref, title, or team, or filter by team. Selecting a ticket loads it into **Ticket details**, linked to the queue. Its human team label then guides the suggestions; use **Unlink** to resolve it as a standalone ticket.
- **Ticket details**: Enter the **Title** and **Description** yourself.

**Advanced options** (collapsed by default) holds the optional settings: an **AI model** to predict the team first, the number of **Similar replies to retrieve** (1-20, default 5), and the **Service category** and **Service subcategory**. When collapsed, any non-default values are summarized next to the toggle.

Click **Generate solution** (or press **Ctrl+Enter** / **⌘+Enter** in the form). The button is enabled once the ticket has a title or description.

**Step 2: Review the draft**

While the reply is drafted, a progress indicator shows the current phase (predicting team, drafting the reply, loading feedback). The review screen then shows:

1. **Draft summary**: Suggested team (with an inline **Reassign** control), category, certainty, and how many past votes shaped the ranking.
2. **Suggested reply**: An editable draft. **Copy** it, **Regenerate** it, or **Export** it.
3. **Ticket**: A compact summary of the ticket. **Edit ticket** returns to step 1 without losing the draft (**Back to draft** returns to it). Clicking step 1 in the progress indicator does the same.
4. **Similar past replies**: The past tickets the draft builds on, with match scores. **Use in draft** replaces the draft with that reply, and **Undo** restores your previous text. Rate each reply as **Helpful** or **Not helpful** to improve future suggestions.

A manual team reassignment is kept if you regenerate the draft.

**Step 3: Send to the team**

Click **Send to {team}** to save the ticket and final reply to the knowledge base. A confirmation screen follows:

- Tickets that came from the queue are removed from it.
- **Resolve next queued ticket** loads the next labeled ticket for review (it does not generate automatically).
- **New ticket** starts over with an empty form. Clicking step 1 in the progress indicator does the same.

---

### 6. Performance Page (`/analytics`)