import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder

# Data preprocessing for the dispatch team endpoint
def dispatch_team(data_path: str, test_set: bool = False, le: LabelEncoder = None, oh: OneHotEncoder = None, classes: list[int | str] = None):
    """
    This function preprocesses the data for the dispatch team endpoint.
    It takes the raw tabular text data and returs a dataframe with embeddings
    for the title and description and one-hot encoded service subcategory and service name.
    """
    
    # Get the labelled data
    df = pd.read_csv(data_path)
    # Keep Ref as stable identifier index
    df.set_index('Ref', inplace=True)

    # Define one-hot encoder and label encoder if not provided
    if not test_set:
        le = LabelEncoder()
        oh = OneHotEncoder(handle_unknown='ignore')

    # Keep only the tickets that never changed the group
    df = df[df['Last team ID->Name'].isna()]

    # Create a column that contains the title and descripiton
    df['Title+Description'] = df['Title_anon'] + df['Description_anon']
    
    if test_set:
        # If the data iselete the rows that don't have the 
        # title and description or Team->Name
        # Test data has to contain all of the categories (also Team->Name)
        df = df.dropna(subset=['Title+Description', 'Team->Name'])
    else:
        # Delete the rows that don't have the title and description
        # Train data doesn't have to contain Team->Name (AL -> dataset not labeled)
        df = df.dropna(subset=['Title+Description'])

    # Embeddings for the Title+Description
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    sentences = df['Title+Description'].astype(str).tolist()
    embeddings = sentence_model.encode(sentences, show_progress_bar=False)
    # Convert to a dataframe aligned to original index
    X = pd.DataFrame(embeddings, index=df.index)
    # Align features to Ref index for downstream .loc usage
    X.index = df.index
    
    if not test_set:
        # If train set, fit the one-hot encoder
        one_hot = oh.fit_transform(df[['Service subcategory->Name', 'Service->Name']])
    else:
        # If test set, transform the one-hot encoder (we have one fitted on train data)
        one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray(), index=df.index)  # keep Ref alignment
    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    # Convert the column names to strings
    X.columns = X.columns.astype(str)

    # If train set, fit the label encoder
    if not test_set:
        classes = [np.nan if x == None else x for x in classes]
        classes = classes + [np.nan]
        le.fit(classes)
        y_true = le.transform(df['Team->Name'])
    else:
        # If test set, use the label encoder fitted on train data
        y_true = df['Team->Name']
    
    # Align labels to Ref index (keeps Ref stable everywhere)
    y_true = pd.Series(y_true, index=df.index)
    
    # Return the preprocessed data, the label encoder, and the one-hot encoder
    return X, y_true, le, oh

# Data preprocessing for the inference endpoint
def inference(df: pd.DataFrame, le: LabelEncoder, oh: OneHotEncoder, sentence_model: SentenceTransformer = None):
    """
    This function preprocesses the data for the inference endpoint.
    It takes the dataframe with pydantic Data model fields and returns a dataframe with embeddings
    for the title and description and one-hot encoded service subcategory and service name.
    """

    # Rename the columns to match the original column names
    df = df.rename(columns={'title_anon': 'Title_anon', 
                            'description_anon': 'Description_anon',
                            'service_subcategory_name': 'Service subcategory->Name',
                            'service_name': 'Service->Name'})

    # Create a column that contains the title and descripiton
    df['Title+Description'] = df['Title_anon'] + df['Description_anon']
    
    # Embeddings for the Title+Description
    if sentence_model is None:
        sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        
    sentences = df['Title+Description'].astype(str).tolist()
    embeddings = sentence_model.encode(sentences, show_progress_bar=False)
    # Convert to a dataframe
    X = pd.DataFrame(embeddings)

    # One-hot encode the service subcategory and service name
    one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray(), index=df.index)  # keep original row alignment

    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    
    # Convert the column names to strings
    X.columns = X.columns.astype(str)
    
    return X
