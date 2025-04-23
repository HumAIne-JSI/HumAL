import requests
import pandas as pd
import numpy as np

# get all of the classes in the dataset
df = pd.read_csv('data/al_demo_train_data.csv')
df.set_index('Ref', inplace=True)
y = pd.read_csv('data/al_demo_train_labels_dispatch.csv')
y.set_index('Ref', inplace=True)
# Replace NaN values with None in the y dataframe (json cannot handle np.nan)
y = y.replace({np.nan: None})


# delete np.nan values
class_list = y['Team->Name'].unique().tolist()
# Remove np.nan or None values from the class list
class_list = [x for x in class_list if pd.notna(x) and x is not None]

# Test initialization endpoint
init_data = {
    "model_name": "svm",
    "qs_strategy": "uncertainty sampling least confidence", 
    "class_list": class_list,
    "train_data_path": "data/al_demo_train_data.csv",
    "test_data_path": "data/al_demo_test_data.csv",
    "al_type": "dispatch"
}
response = requests.post("http://127.0.0.1:8000/activelearning/new", json=init_data)
instance_id = response.json()["instance_id"]
print("\n")
print(f"Created new AL instance with ID: {instance_id}")
print("\n")

# Test getting next instances to label
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=1")
query_indices = response.json()["query_idx"]
print(f"Got instances to label: {query_indices}")
print("\n")

# Test labeling instances
label_data = {
    "query_idx": query_indices,
    "labels": y['Team->Name'].loc[query_indices].tolist()
}
response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)
print(f"Labeled instances response: {response.json()}")
print("\n")

# Test getting model info/performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")

# Test saving model
response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/save")
model_id = response.json()["model_id"]
print(f"Saved model with ID: {model_id}")
print("\n")

# Test inference
test_data = {
    "service_subcategory_name": df['Service subcategory->Name'].iloc[0],
    "team_name": df['Team->Name'].iloc[0],
    "service_name": df['Service->Name'].iloc[0],
    "last_team_id_name": df['Last team ID->Name'].iloc[0],
    "title_anon": df['Title_anon'].iloc[0],
    "description_anon": df['Description_anon'].iloc[0],
    "public_log_anon": df['Public_log_anon'].iloc[0]
}

# Convert numpy nan to None
for key, value in test_data.items():
    if pd.isna(value):
        test_data[key] = None

response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/infer", 
                       params={"model_id": model_id},
                       json=test_data)
print(f"Model predictions: {response.json()}")
print("\n")

response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/infer", 
                       #params={"model_id": },
                       json=test_data)
print(f"Model predictions: {response.json()}")
print("\n")

# label some more instances

for i in range(5):
    response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=1")
    query_indices = response.json()["query_idx"]

    label_data = {
        "query_idx": query_indices,
        "labels": y['Team->Name'].loc[query_indices].tolist()
    }
    response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)

# model performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")

# label some more instances with batch size 3

for i in range(5):
    response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=3")
    query_indices = response.json()["query_idx"]

    label_data = {
        "query_idx": query_indices,
        "labels": y['Team->Name'].loc[query_indices].tolist()
    }
    response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)

# model performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")


#---------------------------------
# Resolution part
#---------------------------------

# create the classes
data_path_train = requests.post("http://127.0.0.1:8000/activelearning/resolution_label_creation?data_path=data/al_demo_train_data.csv&output_data_path=data/al_demo_train_data_res_classes.csv").json()['data_path']
data_path_test = requests.post("http://127.0.0.1:8000/activelearning/resolution_label_creation?data_path=data/al_demo_test_data.csv&output_data_path=data/al_demo_test_data_res_classes.csv").json()['data_path']
data_path_y = requests.post("http://127.0.0.1:8000/activelearning/resolution_label_creation?data_path=data/al_demo_train_labels_resolution.csv&output_data_path=data/al_demo_train_labels_res_classes.csv&labels=True").json()['data_path']
print("\n")
print("Resolution labels created.")
print(f"Labeled train data saved to: {data_path_train}")
print(f"Labeled test data saved to: {data_path_test}")
print(f"Train labels saved to: {data_path_y}")
print("\n")

# get the data
df = pd.read_csv(data_path_train)
df.set_index('Ref', inplace=True)
y = pd.read_csv(data_path_y)
y.set_index('Ref', inplace=True)
y = y.replace({np.nan: None})

# delete np.nan values
class_list = y['label_auto'].unique().tolist()
# Remove np.nan or None values from the class list
class_list = [x for x in class_list if pd.notna(x) and x is not None]

# Test initialization endpoint
init_data = {
    "model_name": "random forest",
    "qs_strategy": "CLUE", 
    "class_list": class_list,
    "train_data_path": data_path_train,
    "test_data_path": data_path_test,
    "al_type": "resolution"
}
response = requests.post("http://127.0.0.1:8000/activelearning/new", json=init_data)
instance_id = response.json()["instance_id"]

print(f"Created new AL instance with ID: {instance_id}")
print("\n")

# Test getting next instances to label
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=1")
query_indices = response.json()["query_idx"]
print(f"Got instances to label: {query_indices}")
print("\n")

# Test labeling instances
label_data = {
    "query_idx": query_indices,
    "labels": y['label_auto'].loc[query_indices].tolist()
}
response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)
print(f"Labeled instances response: {response.json()}")
print("\n")

# Test getting model info/performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")

# Test saving model
response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/save")
model_id = response.json()["model_id"]
print(f"Saved model with ID: {model_id}")
print("\n")

# Test inference
test_data = {
    "service_subcategory_name": df['Service subcategory->Name'].iloc[0],
    "team_name": df['Team->Name'].iloc[0],
    "service_name": df['Service->Name'].iloc[0],
    "last_team_id_name": df['Last team ID->Name'].iloc[0],
    "title_anon": df['Title_anon'].iloc[0],
    "description_anon": df['Description_anon'].iloc[0],
    "public_log_anon": df['Public_log_anon'].iloc[0]
}

# Convert numpy nan to None
for key, value in test_data.items():
    if pd.isna(value):
        test_data[key] = None

response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/infer", 
                       params={"model_id": model_id},
                       json=test_data)
print(f"Model predictions: {response.json()}")
print("\n")

response = requests.post(f"http://127.0.0.1:8000/activelearning/{instance_id}/infer", 
                       #params={"model_id": },
                       json=test_data)
print(f"Model predictions: {response.json()}")
print("\n")

# label some more instances

for i in range(5):
    response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=1")
    query_indices = response.json()["query_idx"]

    label_data = {
        "query_idx": query_indices,
        "labels": y['label_auto'].loc[query_indices].tolist()
    }
    response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)

# model performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")

# label some more instances with batch size 3

for i in range(5):
    response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/next?batch_size=3")
    query_indices = response.json()["query_idx"]

    label_data = {
        "query_idx": query_indices,
        "labels": y['label_auto'].loc[query_indices].tolist()
    }
    response = requests.put(f"http://127.0.0.1:8000/activelearning/{instance_id}/label", json=label_data)

# model performance
response = requests.get(f"http://127.0.0.1:8000/activelearning/{instance_id}/info")
print(f"Model performance info: {response.json()}")
print("\n")