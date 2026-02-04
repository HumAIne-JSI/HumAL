# Backend Changes TODO

This document tracks backend API changes that need to be implemented.

---

## High Priority

### 1. Add `total_count` to instance info endpoint

**Endpoint:** `GET /activelearning/{al_instance_id}/info`

**Current Response:**
```json
{
  "mean_entropies": [...],
  "f1_scores": [...],
  "num_labeled": [63, 65, 115, 165, 315, 465]
}
```

**Expected Response:**
```json
{
  "mean_entropies": [...],
  "f1_scores": [...],
  "num_labeled": [63, 65, 115, 165, 315, 465],
  "model_name": "logistic regression",
  "qs": "random sampling",
  "total_count": 1000,
  "labeled_count": 465
}
```

**Why:** Frontend needs `total_count` to display progress percentage (e.g., "465 / 1000 (46.5%)"). Currently the `/info` endpoint only returns `results_dict` data, missing instance metadata and dataset size.

**Suggested Implementation:**
```python
@router.get("/{al_instance_id}/info")
def get_info(al_instance_id: int):
    if al_instance_id not in al_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    instance_data = al_service.storage.al_instances_dict[al_instance_id]
    
    response = {
        'model_name': instance_data.get('model_name'),
        'qs': instance_data.get('qs'),
        'classes': instance_data.get('classes'),
    }
    
    # Add results data if available
    if al_instance_id in al_service.storage.results_dict:
        results = al_service.storage.results_dict[al_instance_id]
        response.update(results)
    
    # Add total_count and labeled_count from dataset
    if al_instance_id in al_service.storage.dataset_dict:
        dataset = al_service.storage.dataset_dict[al_instance_id]
        y_train = dataset.get('y_train')
        if y_train is not None:
            from skactiveml.utils import MISSING_LABEL
            response['labeled_count'] = int((y_train != MISSING_LABEL).sum())
            response['total_count'] = len(y_train)
    
    return response
```

---

## Medium Priority

### 2. Add `total_count` and `labeled_count` to `/instances` endpoint

**Endpoint:** `GET /activelearning/instances`

**Why:** For consistency and to show progress on Home page instance list.

---

## Low Priority

(Add items here as needed)

---

## Completed

- [ ] None yet

