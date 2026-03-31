from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from skactiveml.pool import UncertaintySampling, RandomSampling, QueryByCommittee, ValueOfInformationEER, Clue
from skactiveml.utils import MISSING_LABEL
import os

RANDOM_STATE = 42

qs_dict = {
    'random sampling': RandomSampling(random_state=RANDOM_STATE, missing_label=MISSING_LABEL),
    'uncertainty sampling entropy': UncertaintySampling(random_state=RANDOM_STATE, missing_label=MISSING_LABEL, method='entropy'),
    'uncertainty sampling margin sampling': UncertaintySampling(random_state=RANDOM_STATE, missing_label=MISSING_LABEL, method='margin_sampling'),
    'uncertainty sampling least confidence': UncertaintySampling(random_state=RANDOM_STATE, missing_label=MISSING_LABEL, method='least_confident'),
    #'query by committee': QueryByCommittee(method='vote_entropy', sample_predictions_method_name='sample_proba', sample_predictions_dict={'n_samples': 50}),
    #'value of information': ValueOfInformationEER(consider_unlabeled=True, consider_labeled=True, candidate_to_labeled=True, subtract_current=True),
    'CLUE': Clue(random_state=RANDOM_STATE, missing_label=MISSING_LABEL)
}

model_dict = {
    'random forest': RandomForestClassifier(random_state=RANDOM_STATE),
    'logistic regression': LogisticRegression(random_state=RANDOM_STATE),
    'svm': SVC(random_state=RANDOM_STATE, probability=True)
}

# ============ AL User/Instance IDs ============
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
GROUND_TRUTH_AL_INSTANCE_ID = 0  # Reserved for global labels


# ============ Tickets ============
TEAM_NAME = "Team->Name"
TEST_SPLIT = "test"
TRAIN_SPLIT = "train"

# ============ MinIO ============
MODELS_BUCKET = "smart-finance-models"
DATA_BUCKET = "smart-finance-data"
def model_location(al_instance_id: int, model_id: int) -> str:
    minio_prefix = _get_minio_prefix()
    if minio_prefix:
        return f"{minio_prefix}/models/{al_instance_id}/{model_id}.joblib"
    return f"models/{al_instance_id}/{model_id}.joblib"

def vectorized_tickets_location(al_instance_id: int, model_id: int, split: str) -> str:
    minio_prefix = _get_minio_prefix()
    if minio_prefix:
        return f"{minio_prefix}/vectorized_tickets/{al_instance_id}/{model_id}_{split}.joblib"
    return f"vectorized_tickets/{al_instance_id}/{model_id}_{split}.joblib"


def _get_minio_prefix() -> str:
    """Get an optional object-key prefix used to namespace MinIO paths."""
    raw_prefix = (os.getenv("MINIO_PREFIX") or "").strip()
    return raw_prefix.strip("/")
