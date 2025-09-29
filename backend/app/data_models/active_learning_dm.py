from pydantic import BaseModel
from typing import Literal, Optional

# Data model for the new instance
class NewInstance(BaseModel):
    model_name: str
    qs_strategy: str
    class_list: list[int | str | None]
    train_data_path: str
    test_data_path: str
    al_type: Literal["dispatch", "resolution"]

# Data model for the label request
class LabelRequest(BaseModel):
    query_idx: list[int | str]
    labels: list[str | int | None]

# Data model for the inference instance input
class Data(BaseModel):
    service_subcategory_name: Optional[str] = None
    team_name: Optional[str] = None
    service_name: Optional[str] = None
    last_team_id_name: Optional[str] = None
    title_anon: Optional[str] = None
    description_anon: Optional[str] = None
    public_log_anon: Optional[str] = None