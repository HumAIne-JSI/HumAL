---
marp: true
title: humAIne — Human-in-the-Loop AI for IT Ticket Triage & Resolution
author: HumAL Team
paginate: true
size: 16:9
theme: default
style: |
  :root {
    --teal: #4aa8a0;
    --navy: #26314f;
    --ink: #1f2430;
    --muted: #5b6472;
    --bg: #f5f7f8;
    --card: #ffffff;
    --accent: #7b5bd6;
  }
  section {
    background: var(--bg);
    color: var(--ink);
    font-family: "Segoe UI", Inter, Roboto, Helvetica, Arial, sans-serif;
    font-size: 26px;
    padding: 52px 60px;
  }
  h1 { color: var(--navy); font-size: 46px; letter-spacing: -0.5px; }
  h2 { color: var(--teal); font-size: 34px; }
  h3 { color: var(--navy); font-size: 26px; margin-bottom: 6px; }
  strong { color: var(--navy); }
  a { color: var(--teal); }
  em { color: var(--muted); }
  table { font-size: 22px; border-collapse: collapse; }
  th { background: var(--navy); color: #fff; }
  td, th { padding: 6px 12px; }
  blockquote {
    border-left: 6px solid var(--teal);
    background: #eef5f4;
    padding: 12px 20px;
    color: var(--ink);
    font-style: normal;
  }
  kbd {
    background: var(--navy); color: #fff; border-radius: 6px;
    padding: 2px 10px; font-size: 20px; font-weight: 700; font-family: inherit;
  }
  .pillars { display: flex; gap: 18px; }
  .pill {
    flex: 1; background: var(--card); border-radius: 14px; padding: 18px 20px;
    border-top: 5px solid var(--teal); box-shadow: 0 4px 14px rgba(38,49,79,0.08);
  }
  .step {
    display: inline-block; background: var(--accent); color: #fff;
    border-radius: 999px; padding: 2px 14px; font-size: 20px; font-weight: 700;
    margin-bottom: 6px;
  }
  .cols { display: flex; gap: 30px; align-items: center; }
  .cols > div { flex: 1; }
  .cols img { width: 100%; height: auto; }
  .flow { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 6px; row-gap: 14px; margin: 10px 0 6px; }
  .node { background: var(--card); border: 2px solid var(--teal); border-radius: 12px; padding: 12px 16px; font-weight: 600; color: var(--navy); font-size: 21px; text-align: center; box-shadow: 0 3px 10px rgba(38,49,79,0.08); }
  .arrow { color: var(--teal); font-size: 28px; font-weight: 700; padding: 0 4px; }
  .loop { text-align: center; color: var(--teal); font-weight: 700; margin: 12px 0; }
  .kpi { color: var(--teal); font-size: 40px; font-weight: 700; }
  footer { color: var(--muted); font-size: 16px; }
  section.title { background: linear-gradient(135deg, #26314f 0%, #34506a 55%, #4aa8a0 100%); color: #fff; }
  section.title h1 { color: #fff; font-size: 54px; }
  section.title h2 { color: #cfeae6; }
  section.title em, section.title strong { color: #eaf3f2; }
  section.section { background: var(--navy); color: #fff; }
  section.section h1 { color: #fff; }
  section.section h2 { color: #8fd6cd; }
  section.shot h2 { font-size: 30px; margin-bottom: 10px; }
  section.shot img { box-shadow: 0 8px 26px rgba(38,49,79,0.18); border-radius: 8px; }
  section.shot p, section.shot li { font-size: 22px; }
  section.dense { font-size: 21px; }
  section.dense h2 { font-size: 28px; }
  section.dense table { font-size: 19px; }
  section.dense td, section.dense th { padding: 4px 10px; }
---

<!-- _class: title -->

![w:340](../images/humaine-logo.png)

# Human-in-the-Loop AI for IT Ticket Triage & Resolution

## AI proposes · Humans decide · The system learns — and proves it

*IT Ticket Manager — AI-Powered Ticket System · Product demo & presenter guide*

<!--
PRESENTER SCRIPT — Opening (30s)
"Hi everyone. Today I'll show humAIne — an AI-powered IT ticket system built around one principle: the AI does the heavy lifting, but a human always stays in control, and every decision is measured."
- Say the tagline out loud: AI proposes, humans decide, the system learns and proves it.
- Tell them the plan: a short story, then a live walkthrough of the app, then the numbers.
- Housekeeping: "I'll take questions at the end, but stop me anytime."
-->

---

<!-- _class: dense -->

## How to run this session

**Agenda (~20 min)** — Story (4 min) → Live walkthrough (12 min) → Metrics & value (4 min) → Q&A.

**Before you start (setup checklist):**
- Start the frontend dev server, open **http://localhost:5173** and sign in.
- Toggle the sidebar switch to **Demo** (orange dot) → the whole app runs on seeded data, **no backend needed**.
- Have two tabs ready: the main app, and **Ticket Evolution** (it opens in a new tab; sign in there with any username and password).
- Zoom the browser to ~110–125% so the room can read the UI.

> This deck doubles as your script — **speaker notes on every slide** contain what to say and what to click.

<!--
PRESENTER SCRIPT — Setup (45s)
- Emphasize Demo mode: "Everything you'll see runs on realistic seeded data, so the demo never depends on a live model or network."
- The green/orange dot in the sidebar is the Live/Demo toggle. Orange = Demo.
- Ticket Evolution opens in its own tab by design (it's the Tier-2 tool, with its own demo sign-in and a Tier-2-only sidebar) — pre-open it and sign in to avoid fumbling.
- Tell the audience these are real screens from the product, not mockups.
- If presenting slides only (no live app), the screenshots carry the full story.
-->

---

## The problem we're solving

- IT service desks are **flooded** with tickets — triage is slow, manual and repetitive.
- Routing to the **wrong team** and writing **first replies** from scratch waste hours every day.
- Teams don't trust **black-box AI** they can't understand or correct.
- Leaders lack the **evidence** to know whether automation is actually working.

> The goal: cut manual effort and resolution time **without** handing control to an opaque model.

<!--
PRESENTER SCRIPT — Problem (1 min)
- Land the pain: "Every mis-routed ticket bounces between teams for hours. Every first reply is written from a blank page."
- Name the two blockers to AI adoption: trust ("is it a black box?") and proof ("is it actually helping?").
- Transition: "So we built the system around solving all four of these at once."
- If you know the audience's numbers (ticket volume, avg handling time), quote them here.
-->

---

## Our answer in one line

> **The AI drafts the triage and the reply. A human stays in control. Every decision teaches the model — and everything is measured.**

<div class="pillars">
<div class="pill">

### 1 · Classify & Resolve
Auto-triage + AI-drafted replies

</div>
<div class="pill">

### 2 · Explain
Show *why*, not just *what*

</div>
<div class="pill">

### 3 · Learn
Human feedback improves the model

</div>
<div class="pill">

### 4 · Prove
Benchmark & measure impact

</div>
</div>

<!--
PRESENTER SCRIPT — Four pillars (45s)
- Read the one-liner slowly; it's the thesis of the whole talk.
- Point to each pillar: Classify & Resolve (the work), Explain (trust), Learn (it gets better), Prove (the numbers).
- Tell them: "The rest of the demo is just these four pillars, shown live."
-->

---

## Who uses it

| Persona | Goal | Where in the app |
|---|---|---|
| **Ticket Labeler / Agent** | Confirm or correct AI triage, fast | Ticket Queue |
| **Support Operator (Tier 2)** | Send a quality first reply in seconds | Ticket Evolution |
| **Team Lead / Analyst** | Track accuracy, effort saved & KPIs | Performance |

*One human-in-the-loop workflow, three points of value.*

<!--
PRESENTER SCRIPT — Personas (30s)
- Anchor each persona to a screen so the audience knows who they are "playing" during the demo.
- "I'll walk you through the app as all three: first the labeler, then the Tier-2 operator, then the team lead."
-->

---

## The journey we'll walk through

<div class="flow">
<div class="node">Login</div>
<div class="arrow">→</div>
<div class="node">Home</div>
<div class="arrow">→</div>
<div class="node">New Project</div>
<div class="arrow">→</div>
<div class="node">Ticket Queue<br/>↻ label &amp; learn</div>
<div class="arrow">→</div>
<div class="node">Ticket Evolution</div>
<div class="arrow">→</div>
<div class="node">Performance</div>
</div>

*The rest of the deck follows this exact path — each screen with the idea behind it, then a close-up of its inputs and buttons.*

<!--
PRESENTER SCRIPT — Journey map (30s)
- Trace the arrows with your cursor/pointer: this is literally the click-path you'll follow live.
- Note the loop on Ticket Queue: labeling feeds back into the model continuously.
- "Every screen has two slides: the big picture, then a close-up of the controls."
-->

---

<!-- _class: section -->

# The flow, step by step

## Each screen — the concept, then the controls

---

<!-- _class: shot -->

<span class="step">Step 1 · Home</span>

## Sign in → the operator's home base

<div class="cols">
<div>

![](../images/screenshots/01-home.png)

</div>
<div>

**Flow:** A secure JWT login opens the **dashboard** — API status, active projects and available AI models — with **quick actions** into every workflow.

</div>
</div>

<!--
PRESENTER SCRIPT — Home (1 min)
What to say: "After signing in, the operator lands on a control tower for the whole system."
What to click / point at:
- Top-left: 'System Status' — API Status badge (Connected), Active Projects count, Available Models count. "Green means the backend is healthy."
- 'Quick Actions' cards jump straight into each workflow.
- 'Your Projects' lists labeling projects with a Trained / In Progress badge and an Open button.
- The Refresh button re-checks system status.
Transition: "Let's create a project — that's where we choose the AI and how it learns."
-->

---

<!-- _class: dense -->

<span class="step">Step 1 · Home — the controls</span>

## What's on the dashboard

| Element | What it tells you / does |
|---|---|
| **System Status → API Status** | Backend health: *Connected / Checking… / Disconnected* |
| **Active Projects** · *X trained* | How many labeling projects exist, how many are trained |
| **Available Models** · *X strategies* | AI models and labeling strategies ready to use |
| **Quick Actions** | Shortcut cards: *Training, Bulk Predictions, Ticket Categorizing, Ticket Resolution* |
| **Your Projects** → **Open** | Jump into an existing project; badge shows *Trained / In Progress* |
| **New Project** / **Refresh** | Start a new project · re-check status |

<!--
PRESENTER SCRIPT — Home controls (30s)
- Use this slide only if the audience is hands-on/technical or asks "what does each part do?"
- For a business audience, skim it: "Status up top, shortcuts in the middle, your projects at the bottom."
-->

---

<!-- _class: shot -->

<span class="step">Step 2 · New Project</span>

## Choose the AI — *and how it learns*

<div class="cols">
<div>

![](../images/screenshots/02-new-project.png)

</div>
<div>

- Pick an **AI Model** and the **Categories (Teams)** to route to.
- Choose a **Labeling Strategy** — *uncertainty, entropy, margin, query-by-committee, random* — deciding **which tickets the AI asks a human about first**.

> This is **active learning**: spend human effort on the most informative tickets.

</div>
</div>

<!--
PRESENTER SCRIPT — New Project (1 min)
What to say: "Setting up a project takes under a minute and it's where the 'human-in-the-loop' magic is configured."
What to click:
- 'AI Model' dropdown → pick a model (e.g., SVM / Logistic Regression). "This is the classifier that will learn to route tickets."
- 'Labeling Strategy' dropdown → pick 'Uncertainty'. KEY POINT: "This decides which tickets we ask the human to label first — the ones the AI is least sure about, so every label teaches it the most."
- 'Categories (Teams)' → click 'Load from Data' to auto-fill the teams from the dataset, or type one and 'Add'.
- Click 'Create Project' → it takes you to the queue.
Note: file upload is disabled in the demo (fixed dataset) — mention if asked.
-->

---

<!-- _class: dense -->

<span class="step">Step 2 · New Project — the controls</span>

## Every input & button

| Control | What it does |
|---|---|
| **AI Model** (dropdown) | The ML algorithm that learns to route tickets |
| **Labeling Strategy** (dropdown) | Picks *which* tickets to ask the human about first (active learning) |
| **Training / Test Data (CSV)** | Data source *(fixed in the demo; upload disabled)* |
| **Download CSV Template** | Gives the exact columns: `title_anon, description_anon, service_name, …` |
| **Categories (Teams)** → **Load from Data** | Auto-fills the routing categories from the dataset |
| **Type a team name… → Add** / chip **✕** | Add or remove categories manually |
| **Create Project** | Creates the instance and opens the Ticket Queue *(needs model + strategy + categories)* |

<!--
PRESENTER SCRIPT — New Project controls (40s)
- 'Load from Data' is the fast path — one click fills all the teams.
- The 'Create Project' button stays disabled until model + strategy + at least one category are set — a good moment to explain the minimum recipe.
- If asked about real data onboarding: "In production you upload your own CSV; the template button shows the exact format."
-->

---

<!-- _class: shot -->

<span class="step">Step 3 · Ticket Queue</span>

## AI triage — *Classification*

<div class="cols">
<div>

![](../images/screenshots/03-ticket-queue.png)

</div>
<div>

The AI answers **two questions at once**, each with a **confidence score**: **what kind of ticket** (13+ types) and **which team** handles it (17 teams). Here: **Application Support · 84%**, with a top‑3 breakdown.

> Powered by sentence embeddings + fine-tuned language models — no hand-written rules.

</div>
</div>

<!--
PRESENTER SCRIPT — Ticket Queue (1.5 min)
What to say: "This is where a labeler spends their day — and where the AI earns its trust."
What to click:
- Select the first ticket in the list. The right panel shows the ticket, then the AI's suggestion.
- Point at the ranked suggestions and their confidence percentages. "The top team is selected, and the runner-up is available if it fits better."
- 'Get AI Suggestion' re-runs the model if needed. The top suggestion is pre-selected; pick another (keys 1–2) or search any team (/), then 'Assign' (↵) commits it.
- The selected row has a distinct border and radio indicator; the summary repeats the team that Assign will save.
Transition: "But would you trust 84% without knowing why? That's the next screen."
-->

---

<!-- _class: dense -->

<span class="step">Step 3 · Ticket Queue — the controls</span>

## Find, decide, move on

| Control | What it does |
|---|---|
| **Search / Filters / Sort** | Find tickets; sort by *Newest* or *Certainty (High→Low)* |
| **Get AI Suggestion** | Runs the model on the selected ticket |
| **Suggestions** (<kbd>1</kbd>–<kbd>2</kbd>) · **Another team** (<kbd>/</kbd>) | Select the AI's pick, its runner-up, or any team — nothing saves yet |
| **Assign** (<kbd>↵</kbd>) · <kbd>Esc</kbd> to undo | Commit the selected team as the label, then move on |
| **Tired · Difficult** flags · **Skip — I don't know** | Flag the label you assign, or skip instead of guessing |
| **Bulk select** (<kbd>x</kbd>) · **Select all** (<kbd>Shift</kbd>+<kbd>a</kbd>) | Label many tickets at once |
| **Break modal** | Nudges a pause — *"quality matters more than speed"* |

<!--
PRESENTER SCRIPT — Queue controls (45s)
- Tired and Difficult are flags sent with the next assigned label. 'Skip — I don't know' moves on without guessing a team.
- Bulk actions + keyboard selection make high-volume labeling fast — show 'x' for bulk, or '2' then Enter to assign the runner-up, if time allows.
- The Break modal shows we care about labeler wellbeing and label quality, not just throughput.
-->

---

<!-- _class: shot -->

<span class="step">Step 3 · detail</span>

## "Why this suggestion?" — *Explainability*

<div class="cols">
<div>

![](../images/screenshots/03-ticket-queue.png)

</div>
<div>

- **Highlighted words** show what **supports** vs. **opposes** the prediction.
- The **closest past ticket (86% match)** gives the agent concrete evidence.
- Toggle **Show / Hide Details** to expand the word-by-word weights.

> No black box — explanations build trust, speed decisions, and help catch mistakes.

</div>
</div>

<!--
PRESENTER SCRIPT — Explainability (1 min)
What to say: "This is the trust layer — the difference between 'the AI said so' and 'here's why.'"
What to click / point at:
- 'Why this suggestion?' panel — the highlighted words are what drove the prediction (LIME). Green supports, red opposes.
- 'Similar Tickets by Category' — the closest resolved ticket for each top guess, with a match %. "The labeler can open a real precedent."
- Toggle 'Show Details' for the ranked word weights.
Key line: "When the AI is wrong, the explanation makes it obvious — the labeler catches it in seconds instead of trusting blindly."
-->

---

<!-- _class: dense -->

<span class="step">Power-user tip</span>

## Keyboard shortcuts — label at speed

| Key | Action | | Key | Action |
|---|---|---|---|---|
| <kbd>j</kbd> / <kbd>↓</kbd> | Next ticket | | <kbd>1</kbd> / <kbd>2</kbd> | Select suggestion 1 / 2 |
| <kbd>k</kbd> / <kbd>↑</kbd> | Previous ticket | | <kbd>/</kbd> | Search all teams |
| <kbd>x</kbd> | Toggle bulk select | | <kbd>↵</kbd> | Assign the selected team |
| <kbd>Shift</kbd>+<kbd>a</kbd> | Select all visible | | <kbd>?</kbd> | Show shortcuts |
| <kbd>Esc</kbd> | Undo a changed team, then close / clear | | | |

*A trained labeler never leaves the keyboard — read, decide, next.*

<!--
PRESENTER SCRIPT — Shortcuts (20s)
- Optional slide; great for an operations audience worried about speed.
- "Switching teams never saves by itself. Enter commits the current selection; 2 then Enter takes the runner-up."
-->

---

<span class="step">Step 4 · Assign or correct</span>

## The learning loop — *Human feedback*

<div class="flow">
<div class="node">Strategy picks the<br/>most useful ticket</div>
<div class="arrow">→</div>
<div class="node">Agent reviews<br/>AI + explanation</div>
<div class="arrow">→</div>
<div class="node">Confirm or<br/>override</div>
<div class="arrow">→</div>
<div class="node">Model<br/>retrains</div>
<div class="arrow">→</div>
<div class="node">Accuracy up,<br/>uncertainty down</div>
</div>

<p class="loop">↻ repeats — every click makes the model better</p>

**Every click is feedback.** The model retrains, grows more confident, and reaches target accuracy with **fewer labels** than random sampling — human effort goes only where the model is unsure.

<!--
PRESENTER SCRIPT — Learning loop (45s)
- This is the "Learn" pillar. Walk the arrows.
- The punchline: because the strategy picks the *most informative* tickets, we hit target accuracy with far fewer labels than labeling at random — that's real human time saved.
- "Confirm teaches it it's right; override teaches it it's wrong. Both are gold."
-->

---

<!-- _class: shot -->

<span class="step">Step 5 · Manual Queue</span>

## Bootstrap & ground truth

<div class="cols">
<div>

![](../images/screenshots/04-manual-queue.png)

</div>
<div>

**Flow:** The same queue **without AI** — search for the team and **Assign** it. Used to gather the first labels before the model is trained, or to check the model against unaided human judgment.

</div>
</div>

<!--
PRESENTER SCRIPT — Manual Queue (40s)
What to say: "Before the AI knows anything, we need a few honest human labels — that's the Manual Queue."
- No predictions, no explanations — just the ticket, a team search, and 'Assign'.
- Two uses: (1) bootstrap the very first training data, (2) audit — hide the AI to measure unaided human accuracy as a baseline.
- Same keyboard shortcuts as the AI queue, minus the suggestion keys: / to search, Enter to assign.
-->

---

<!-- _class: shot -->

<span class="step">Step 6 · Ticket Evolution</span>

## An AI-drafted first reply — *Resolution*

<div class="cols">
<div>

![](../images/screenshots/06-ticket-evolution.png)

</div>
<div>

1. **Retrieve** similar past tickets
2. **Rank** by meaning + category + quality
3. **Draft** a reply
4. **Human approves / edits**

Here: `vpn_request` → *Network Access* (72%) with a ready-to-send reply.

> Each approved answer **instantly grows the knowledge base**.

</div>
</div>

<!--
PRESENTER SCRIPT — Ticket Evolution (1.5 min)
What to say: "Now the Tier-2 operator's tool — turning a routed ticket into a sent reply in seconds."
What to click:
- Pick a ticket you just labeled from the 'From queue' tab, or type a Title + Description in 'Ticket details'.
- Click 'Generate solution' (or Ctrl+Enter); the header steps move to 'Review draft'.
- Walk the draft summary: 'Suggested team' = Network Access (with an inline 'Reassign'), 'Category' = vpn_request, 'Certainty' 72%, and 'Past feedback' showing how many votes shaped the ranking.
- The 'Suggested reply' is a ready-to-send draft the operator can edit.
- Alongside: 'Similar past replies' with match % and 👍/👎 votes — real precedents.
- Click 'Send to Network Access' → the confirmation screen offers 'Resolve next queued ticket'.
Key line: "Approve it and it joins the knowledge base — the next similar ticket gets an even better draft. No retraining wait."
-->

---

<!-- _class: dense -->

<span class="step">Step 6 · Ticket Evolution — the controls</span>

## From ticket to sent reply

| Control | What it does |
|---|---|
| **From queue · Ticket details** | Pull a ticket you already labeled, or type one in *(title or description required)* |
| **Advanced options → AI model** | Predict the team with a trained model first |
| **Advanced options → Similar replies to retrieve** (1–20) | How many similar past replies to pull |
| **Advanced options → Service category / subcategory** | Sharpen retrieval to the right area |
| **Generate solution** (Ctrl+Enter) | Classify + draft a reply + fetch precedents |
| **Certainty · Past feedback** | Team confidence · how many community votes shaped the ranking |
| **Suggested reply** → **Copy · Regenerate · Export · Send to {team}** | Edit & use the draft; *Send* saves it to the KB |
| **Similar past replies** → 👍 / 👎 · **Use in draft** | Rate a precedent or reuse it (with Undo) |
| **Resolve next queued ticket** | After sending, load the next labeled ticket |

<!--
PRESENTER SCRIPT — Resolution controls (45s)
- 'Similar replies to retrieve' = the top-K knob for the RAG search; more = more precedents, slower.
- 'Send to {team}' is the money button: it saves the approved reply and grows the knowledge base incrementally.
- 👍/👎 on precedents feed future rankings — the community teaches the retrieval what's actually helpful.
-->

---

<!-- _class: shot -->

<span class="step">Step 7 · Performance</span>

## Proving it works — *Benchmarking*

<div class="cols">
<div>

![](../images/screenshots/05-analytics.png)

</div>
<div>

Four pillars, live:
- **Model performance** — F1, uncertainty
- **Resource efficiency** — labels/hour, samples-to-target
- **Human satisfaction** — accept vs. override
- **Programme KPIs** vs. targets

</div>
</div>

<!--
PRESENTER SCRIPT — Performance (1 min)
What to say: "Every click in the demo is instrumented — this page turns it into evidence."
What to point at:
- Top: 'Key results vs targets' scorecards with On track / At risk badges.
- Three pillar cards: Model performance (F1 + trend), Resource efficiency (labels to reach quality), Human satisfaction (agreement %).
- 'Export' saves a JSON snapshot for reporting.
- Note the Demo/Live badge — here it's demo data; in production it reads from the live analytics API.
-->

---

<!-- _class: dense -->

<span class="step">Step 7 · Performance — the KPIs</span>

## Reading the scorecards

Each KPI shows a **value**, a **target** and a **status** — **On track** · *At risk* · *Off target* · *No data*.

| KPI | What it measures | Target |
|---|---|---|
| **F1 score** | Overall routing accuracy across all teams | ≥ 0.80 |
| **Auto-solve rate** | Tickets fully resolved by AI, no human touch | ≥ 60% |
| **AI-managed rate** | Tickets handled with AI assistance | ≥ 30% |
| **Resolution-time reduction** | Faster handling vs. the manual baseline | ≥ 40% |
| **Reopen rate** | Closed tickets that bounce back *(quality guardrail)* | ≤ 10% |
| **Manual-effort reduction** | Human time saved vs. baseline | ≥ 50% |
| **Trust / Satisfaction** | Operator confidence & sentiment in the AI | ≥ 80% / 75% |

*Three headline pillars back these up: **Model performance** (F1 + trend) · **Resource efficiency** (labels to reach 0.80, decisions/hour) · **Human satisfaction** (acceptance %).*

<!--
PRESENTER SCRIPT — KPI detail (1 min)
What to say: "Each card is a promise with a number and a target — green when we're on track, amber when at risk."
Walk a few:
- 'F1 score' is the single best measure of routing accuracy; target 0.80.
- 'Auto-solve' and 'AI-managed' show how much work the AI takes off the team's plate (60% / 30% targets).
- 'Reopen rate' is the safety guardrail — if auto-solved tickets bounce back above 10%, we pull back automation.
- 'Manual-effort reduction' and 'Trust/Satisfaction' close the loop: less work, and people actually trust it.
Key line: "Every one of these is computed from the clicks you saw earlier — nothing here is hand-entered."
Reminder: these are programme TARGETS; swap in live values from a real run when you have them.
-->

---

## Human–AI collaboration, quantified

- **Acceptance vs. override by confidence** — proves the model learns *when* to be trusted.
- **Decision time: AI-aided vs. manual** — how much explanations speed agents up.
- **Explainability lift** — acceptance is higher when the explanation was viewed.
- **Auto-close** — high-confidence tickets (≥ 85%) resolve without human touch; **reopen rate** is the safety check.

> A repeatable **benchmarking suite** replays realistic scenarios to compare strategies and models fairly.

<!--
PRESENTER SCRIPT — Collaboration metrics (45s)
- These are the metrics that make leadership comfortable: not just "is the model accurate" but "is the human+AI team working well?"
- Auto-close with a reopen-rate guardrail is the safe path to automation: only very confident tickets, and we watch how many come back.
- The benchmarking suite means we can A/B strategies and models on the same scenarios — fair, repeatable comparisons.
-->

---

## Progress against programme targets

<div class="pillars">
<div class="pill">

<div class="kpi">60%</div>
Tickets **auto-solved** by AI

</div>
<div class="pill">

<div class="kpi">−40%</div>
**Resolution time** reduction

</div>
<div class="pill">

<div class="kpi">≤10%</div>
**Reopen rate** ceiling

</div>
<div class="pill">

<div class="kpi">80%</div>
User **trust** in the AI

</div>
</div>

*Illustrative programme (AFU) targets. Sample benchmark run: F1 0.83 · Accuracy 0.86 · AUROC 0.89.*

<!--
PRESENTER SCRIPT — Targets (30s)
- Be explicit these are programme TARGETS, not claims — swap in your real numbers if you have a run.
- The sample benchmark (F1 0.83 / Acc 0.86 / AUROC 0.89) is illustrative of a mid-training checkpoint.
- Frame: "This is how we'll know the programme succeeded."
-->

---

<!-- _class: dense -->

## Live demo — the exact click-path

1. **Login** → **Home**: point at System Status (API, projects, models).
2. **New Project**: pick *AI Model* + *Labeling Strategy* → *Load from Data* → **Create Project**.
3. **Ticket Queue**: select a ticket → read **84%** suggestion → open **Why this suggestion?** → **Assign** (<kbd>↵</kbd>) the AI's pick on one; search another team (<kbd>/</kbd>) and **Assign** on the next.
4. **Ticket Evolution** *(new tab)*: pick or enter a ticket → **Generate solution** → review the draft + precedents → **Send to {team}** → **Resolve next queued ticket**.
5. **Performance**: walk the scorecards → **Export** a snapshot.

> **Fallback:** if anything misbehaves live, the screenshots in this deck reproduce every step.

<!--
PRESENTER SCRIPT — Click-path cheat sheet (keep visible while demoing)
- This is your safety net — glance here if you lose your place.
- Keep Demo mode ON the whole time so nothing depends on the backend.
- Budget ~12 minutes for the live walkthrough; don't rabbit-hole on any one screen.
-->

---

<!-- _class: dense -->

## Anticipated questions

| They ask… | Say… |
|---|---|
| *"Is our data safe?"* | Tickets are anonymised (`*_anon` fields); runs on-prem with MinIO/DuckDB. |
| *"What if the AI is wrong?"* | The human confirms/overrides every label; explanations expose bad calls. |
| *"Does it need lots of labeled data?"* | No — active learning reaches target accuracy with far fewer labels. |
| *"What model writes the replies?"* | Retrieval (RAG) over past tickets + an LLM draft the human always edits. |
| *"How do we know it's working?"* | The Performance page + benchmarking suite — accuracy, effort, trust. |
| *"Can it fully automate?"* | Only high-confidence tickets auto-close, with reopen-rate as a guardrail. |

<!--
PRESENTER SCRIPT — FAQ (use as needed)
- Keep answers short and route back to a screen you already showed.
- Privacy and "what if it's wrong" are the two most common; lead with those.
-->

---

## Business value

<div class="pillars">
<div class="pill">

### Less manual effort
AI triages and drafts; humans review instead of starting from zero.

</div>
<div class="pill">

### Faster resolutions
Right team, first time — with a ready-to-send reply.

</div>
<div class="pill">

### Trust by design
Every decision is explained and every outcome is measured.

</div>
</div>

> Continuous improvement: the system gets **more capable and more trusted** the more it's used.

<!--
PRESENTER SCRIPT — Business value (30s)
- Tie back to the four pillars and the opening pain points.
- One sentence per tile; don't over-explain — the demo already proved it.
-->

---

## Architecture at a glance

![w:760](../images/smart_ticketing_architecture.svg)

*Vue frontend · FastAPI backend · semantic search (FAISS) + language models (DistilBERT) · LLM-drafted replies · MinIO / DuckDB / RabbitMQ for storage & async jobs.*

<!--
PRESENTER SCRIPT — Architecture (30s, optional)
- Only linger here for a technical audience.
- Keep it one breath: Vue front end, FastAPI back end, FAISS for similarity, DistilBERT for classification, an LLM for drafting, and MinIO/DuckDB/RabbitMQ for storage and async jobs.
-->

---

<!-- _class: title -->

# Thank you

## Key takeaways

- **Classify & resolve** tickets automatically — with confidence.
- **Explain** every suggestion — no black box.
- **Learn** from human feedback — smarter every day.
- **Prove** the impact — accuracy, effort saved, trust.

*Questions & discussion*

<!--
PRESENTER SCRIPT — Close (30s)
- Recap the four pillars in one line each.
- Clear call to action: propose next step (pilot on a real team / dataset).
- "Happy to dive into any screen again — what would you like to see?"
-->
