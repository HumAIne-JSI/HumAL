# HumAL User Guide

## Introduction

Welcome to HumAL, an integrated platform for training machine learning models with human feedback.

This guide will help you understand and use all features of the platform effectively.

---

## Getting Started

### Prerequisites
- HumAL installed and running (see [README.md](../README.md) for installation)
- Backend API running at `http://localhost:8000`
- Data loaded in `backend/data/`
---

## Application Overview

HumAL API provides the following capabilities:

1. **Active Learning** - Create and manage active learning instances for model training
2. **Dispatch Labeling** - Label tickets for team routing
3. **Inference** - Run predictions on new tickets using trained models

---

## API Endpoints Guide

### Active Learning

Use the Active Learning API to:
- Create new AL instances with `POST /activelearning/new`
- Get informative samples with `GET /activelearning/{al_instance_id}/next`
- Submit labels with `PUT /activelearning/{al_instance_id}/label`
- Run inference with `POST /activelearning/{al_instance_id}/infer`

See [API.md](API.md) for detailed endpoint documentation.

### Labeling and Inference

The labeling workflow:
1. Query the next sample to label: `GET /activelearning/{al_instance_id}/next`
2. Retrieve ticket data: `POST /data/{al_instance_id}/tickets`
3. Submit labels: `PUT /activelearning/{al_instance_id}/label`
4. Get explanations: `POST /xai/{al_instance_id}/explain_lime`

### Inference

Run predictions on new tickets using a trained model:
- `POST /activelearning/{al_instance_id}/infer` - Get model predictions
- `POST /xai/{al_instance_id}/explain_lime` - Get LIME explanations
- `POST /xai/{al_instance_id}/nearest_ticket` - Find similar training examples

See [API.md](API.md) for complete endpoint documentation.
