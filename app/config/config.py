from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from skactiveml.pool import UncertaintySampling, RandomSampling, QueryByCommittee, ValueOfInformationEER, Clue
from skactiveml.utils import MISSING_LABEL

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