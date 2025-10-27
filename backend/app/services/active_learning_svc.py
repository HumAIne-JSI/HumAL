from skactiveml.classifier import SklearnClassifier
from skactiveml.utils import MISSING_LABEL
import numpy as np
import joblib
import os
from app.data_models.active_learning_dm import NewInstance, LabelRequest
from app.services.data_preprocessing import dispatch_team, resolution
from app.config.config import model_dict, qs_dict
import pandas as pd
from sklearn.metrics import f1_score
from scipy.stats import entropy
from app.core.storage import ActiveLearningStorage

class ActiveLearningService:
    def __init__(self, storage: ActiveLearningStorage):
        self.storage = storage

    # Logic for creating a new active learning instance
    def create_instance(self, new_instance: NewInstance):
        # Get next available instance ID
        instance_id = self.storage.get_next_instance_id()
        
        # Define the classes as integers
        new_instance.class_list = new_instance.class_list
        classes = list(range(len(new_instance.class_list)+1))
        
        # Initialize active learning instance
        self.storage.al_instances_dict[instance_id] = {
            'model': model_dict[new_instance.model_name],
            'model_name': new_instance.model_name,
            'qs': new_instance.qs_strategy,
            'classes': classes,
            'al_type': new_instance.al_type
        }
        
        # Preprocess the data
        if new_instance.al_type == "dispatch":
            X_train, y_train, le, oh, index_dict_train = dispatch_team(new_instance.train_data_path, test_set=False, classes=new_instance.class_list)
            X_test, y_test, _, _, _ = dispatch_team(new_instance.test_data_path, test_set=True, le=le, oh=oh)
        else:
            X_train, y_train, le, oh, index_dict_train = resolution(new_instance.train_data_path, test_set=False, classes=new_instance.class_list)
            X_test, y_test, _, _, _ = resolution(new_instance.test_data_path, test_set=True, le=le, oh=oh)
        
        # Get the index of np.nan in the LabelEncoder's classes
        empty = le.transform([np.nan])[0]
        # Replace missing values with MISSING_LABEL in y_train
        y_train = pd.Series(y_train).replace(empty, MISSING_LABEL)
        
        # Dictionary that maps from original index to encoded index
        index_dict_train_inv = {v: k for k, v in index_dict_train.items()}
        
        # save the data to the dataset dictionary
        self.storage.dataset_dict[instance_id] = {
            'X_train': X_train,
            'y_train': y_train,
            'X_test': X_test,
            'y_test': y_test,
            'le': le,
            'oh': oh,
            'index_dict_train': index_dict_train,
            'index_dict_train_inv': index_dict_train_inv,
            'train_data_path': new_instance.train_data_path,
            'test_data_path': new_instance.test_data_path
        }
        
        return instance_id

    # Logic for getting the next instances
    def get_next_instances(self, al_instance_id: int, batch_size: int = 1):        
        # Get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        
        # Get the query strategy, model and classes
        instance = self.storage.al_instances_dict[al_instance_id]
        qs_name = instance['qs']
        qs = qs_dict[qs_name]
        model = instance['model']
        classes = instance['classes']
        
        # Initialize classifier
        clf = SklearnClassifier(model, classes=classes)
        
        # Get the query indices
        if qs_name == 'random sampling':
            query_idx = qs.query(X=X, y=y, batch_size=batch_size)
        #elif qs_name == 'query by committee':
        #    query_idx = qs.query(X=X, y=y, batch_size=batch_size, ensemble=qb_c)
        elif qs_name == 'value of information':
            query_idx = qs.query(X=X, y=y, clf=clf, ignore_partial_fit=True, batch_size=batch_size)
        else:
            query_idx = qs.query(X=X, y=y, batch_size=batch_size, clf=clf)
        
        # convert the query_idx to the original index
        query_idx = [self.storage.dataset_dict[al_instance_id]['index_dict_train'][idx] for idx in query_idx]
        
        # Return the query indices
        return query_idx

    # Logic for labeling instances
    def label_instance(self, al_instance_id: int, label_request: LabelRequest):
        # get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        X_test = self.storage.dataset_dict[al_instance_id]['X_test']
        y_test = self.storage.dataset_dict[al_instance_id]['y_test']
        
        # Get the query indices and labels
        query_idx = label_request.query_idx
        labels = label_request.labels
        # change None to np.nan
        labels = [np.nan if label is None else label for label in labels]
        
        le = self.storage.dataset_dict[al_instance_id]['le']
        # convert the labels to integers
        labels = le.transform(labels)
        
        # convert the original index to the new index
        query_idx = [self.storage.dataset_dict[al_instance_id]['index_dict_train_inv'][idx] for idx in query_idx]
        
        if al_instance_id not in self.storage.al_instances_dict:
            return {"error": "Instance not found"}
        
        instance = self.storage.al_instances_dict[al_instance_id]
        
        # update the labels
        for idx, label in zip(query_idx, labels):
            y.iloc[idx] = label

    # Logic for updating the model
    def update_model(self, al_instance_id: int):
        # Instance
        instance = self.storage.al_instances_dict[al_instance_id]

        # get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        
        # get the model
        model = instance['model']
        clf = SklearnClassifier(model, classes=instance['classes'])

        # Train the model
        clf.fit(X, y)
        
        # create the model directory if it doesn't exist
        os.makedirs(f'models/{al_instance_id}', exist_ok=True)
        
        # save the model (the clf object)
        model_path = f'models/{al_instance_id}/0.pkl'
        joblib.dump(clf, model_path)
        
        # save the model path
        if al_instance_id not in self.storage.model_paths_dict:
            self.storage.model_paths_dict[al_instance_id] = {}
        self.storage.model_paths_dict[al_instance_id][0] = model_path


    def calculate_metrics(self, al_instance_id: int):
        # Get the data
        X_test = self.storage.dataset_dict[al_instance_id]['X_test']
        y_test = self.storage.dataset_dict[al_instance_id]['y_test']
        y = self.storage.dataset_dict[al_instance_id]['y_train']

        # Get the label encoder
        le = self.storage.dataset_dict[al_instance_id]['le']

        # Get the model
        model_path = self.storage.model_paths_dict[al_instance_id][0]
        clf = joblib.load(model_path)

        # calculate the entropy of the model
        mean_entropy = np.mean(entropy(clf.predict_proba(X_test), axis=1))
        
        # calculate the number of labeled instances
        num_labeled = int(y.value_counts().sum())
        
        # save the mean entropy
        if al_instance_id not in self.storage.results_dict:
            self.storage.results_dict[al_instance_id] = {
                "mean_entropies": [],
                "f1_scores": [],
                "num_labeled": []
            }
        self.storage.results_dict[al_instance_id]["mean_entropies"].append(mean_entropy)
        
        self.storage.results_dict[al_instance_id]["num_labeled"].append(num_labeled)
        # calculate the f1 score of the model
        predictions = clf.predict(X_test)
        
        # Handle NaN values in y_test before calculating f1_score
        # Check if y_test contains string values or numerical values
        if y_test.dtype.kind in ['U', 'S', 'O']:  # String or object dtype
            # For string values, replace NaN with "NotANumber"
            y_test = np.array(["NotANumber" if pd.isna(val) else val for val in y_test])
        else:  # Numerical dtype
            # For numerical values, replace NaN with inf
            y_test = np.array([float('inf') if pd.isna(val) else val for val in y_test])
        
        f1 = f1_score(y_test, le.inverse_transform(predictions), average='macro')
        self.storage.results_dict[al_instance_id]["f1_scores"].append(f1)


    # Logic for saving the model
    def save_model(self, al_instance_id: int):
        if al_instance_id not in self.storage.model_paths_dict:
            self.storage.model_paths_dict[al_instance_id] = {}

        # Get the current model
        current_model = joblib.load(self.storage.model_paths_dict[al_instance_id][0])
        
        # Save the model
        model_id = max(self.storage.model_paths_dict[al_instance_id].keys()) + 1
        model_path = f'models/{al_instance_id}/{model_id}.pkl'
        joblib.dump(current_model, model_path)
        
        # Save the model path
        self.storage.model_paths_dict[al_instance_id][model_id] = model_path

        return model_id
    
    # Logic for deleting an active learning instance
    def delete_instance(self, al_instance_id: int):
        # delete the instance from the dictionaries
        del self.storage.al_instances_dict[al_instance_id]
        del self.storage.dataset_dict[al_instance_id]
        del self.storage.results_dict[al_instance_id]
        
        # delete the saved models
        for model_id in self.storage.model_paths_dict[al_instance_id].keys():
            os.remove(self.storage.model_paths_dict[al_instance_id][model_id])
        
        # delete the model dictionary
        del self.storage.model_paths_dict[al_instance_id]
