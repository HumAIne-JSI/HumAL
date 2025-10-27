import pandas as pd
import numpy as np
import re
import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import normalize
from sklearn.preprocessing import OneHotEncoder
from app.utils.text_preprocessing_helpers import extract_first_reply,  remove_name_number_at_beggining, clean, extract_initial_sequence, categorize_text

# Data preprocessing for the dispatch team endpoint
def dispatch_team(data_path: str, test_set: bool = False, le: LabelEncoder = None, oh: OneHotEncoder = None, classes: list[int | str] = None):
    """
    This function preprocesses the data for the dispatch team endpoint.
    It takes the raw tabular text data and returs a dataframe with embeddings
    for the title and description and one-hot encoded service subcategory and service name.
    """
    
    # Get the labelled data
    df = pd.read_csv(data_path)
    # Set the 'Ref' column as the index
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

    # Reset the index (embeddings require a sequential index)
    df = df.reset_index(names=['original_index'])

    # Dictionary which enables to map the new index to the original index
    # Used later for tracking the ticket Ref number
    original_index = df['original_index']
    new_index = df.index
    index_dict = dict(zip(new_index, original_index))
    
    # Embeddings for the Title+Description
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = sentence_model.encode(df['Title+Description'], show_progress_bar=False)
    # Convert to a dataframe
    X = pd.DataFrame(embeddings)
    
    if not test_set:
        # If train set, fit the one-hot encoder
        one_hot = oh.fit_transform(df[['Service subcategory->Name', 'Service->Name']])
    else:
        # If test set, transform the one-hot encoder (we have one fitted on train data)
        one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray())
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
    
    # Return the preprocessed data, the label encoder, the one-hot encoder, and the index dictionary
    return X, y_true, le, oh, index_dict

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
        
    embeddings = sentence_model.encode(df['Title+Description'], show_progress_bar=False)
    # Convert to a dataframe
    X = pd.DataFrame(embeddings)

    # One-hot encode the service subcategory and service name
    one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray())

    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    
    # Convert the column names to strings
    X.columns = X.columns.astype(str)
    
    return X

# Data preprocessing for the resolution label creation
def resolution_label_creation(data_path: str, output_data_path: str, labels: bool = False, test_set: bool = False):
    """
    This function creates the resolution labels for the tickets.
    It takes the raw tabular text data and returns a dataframe with the resolution labels.
    The labels are created based on the first reply to the ticket and it's starting sequence.

    This function can also accept only the first replies column
    """
    
    # Get the data
    df = pd.read_csv(data_path)
    df.set_index('Ref', inplace=True)
    
    # If the data does not contain only the first replies,
    # keep only the tickets that didn't change the group (otherwise this column is not available)
    if not labels:
        df = df[df['Last team ID->Name'].isna()]

    # Extract the first reply from the text
    df['first_reply'] = df['Public_log_anon'].apply(extract_first_reply)
    
    # Remove the beginning of the answers
    df['first_reply'] = df['first_reply'].apply(remove_name_number_at_beggining)
    
    # Remove the certain pattern from the text ("Below you will find...")
    df['first_reply'] = df['first_reply'].apply(clean)
    
    # Extract the initial sequences and create a new column with this sequence
    df['initial_sequence'] = df['first_reply'].apply(extract_initial_sequence)
    
    # Create a mapping from initial sequences to group numbers
    sequence_mapping = {seq: idx for idx, seq in enumerate(df['initial_sequence'].unique())}
    
    # Assign group numbers based on the initial sequences
    df['initial_sequence'] = df['initial_sequence'].map(sequence_mapping)
    
    # Create the labels based on the first reply
    df[['label_auto', 'label_category']] = df['first_reply'].apply(categorize_text).apply(pd.Series)

    if test_set:
        # Drop the rows that don't have the label_auto
        # Test data has to contain the label_auto
        df = df.dropna(subset=['label_auto'])

    # Save the dataframe
    df.to_csv(output_data_path, index=True)

    return output_data_path

# Data preprocessing for the resolution endpoint (can be called after resolution_label_creation)
def resolution(data_path: str, test_set: bool = False, le: LabelEncoder = None, oh: OneHotEncoder = None, classes: list[int | str] = None):   
    """
    This function preprocesses the data for the resolution endpoint.
    It takes the raw tabular text data and returns a dataframe with embeddings
    for the title and description and one-hot encoded service subcategory and service name.
    """
    
    # Get the data 
    df = pd.read_csv(data_path)
    df.set_index('Ref', inplace=True)

    # Define one-hot encoder and label encoder if not provided
    if not test_set:
        le = LabelEncoder()
        oh = OneHotEncoder(handle_unknown='ignore')
    
    # reset the index
    df = df.reset_index(names=['original_index'])
    
    # Create a dictionary that maps the new index to the original index
    # Used later for tracking the ticket Ref number
    original_index = df['original_index']
    new_index = df.index
    index_dict = dict(zip(new_index, original_index))

    # Create a column that contains the title and descripiton
    df['Title+Description'] = df['Title_anon'] + df['Description_anon']
    
    # Embeddings for the Title+Description
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = sentence_model.encode(df['Title+Description'], show_progress_bar=False)
    # Normalize the embeddings
    embeddings = normalize(embeddings, norm='l2')
    # Convert to a dataframe
    X = pd.DataFrame(embeddings)
    
    # One-hot encode other features    
    if not test_set:
        one_hot = oh.fit_transform(df[['Service subcategory->Name', 'Service->Name']])
    else:
        one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray())

    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    # Convert the column names to strings
    X.columns = X.columns.astype(str)
    
    if not test_set:
        # Fit the label encoder (if train set)
        classes = [np.nan if x == None else x for x in classes]
        classes = classes + [np.nan]
        le.fit(classes)
        y_true = le.transform(df['label_auto'])
    else:
        # Use the label encoder fitted on train data (if test set)
        y_true = df['label_auto']
    
    return X, y_true, le, oh, index_dict