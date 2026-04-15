"""
Portable TicketVectorizer - Standalone module for XAI integration.

This module provides a TicketVectorizer class that can be serialized with cloudpickle
to external machines without module dependencies. The class is agnostic to how it's
deserialized - it can be loaded from bytecode without importing 'humal_vectorizer'.

The TicketVectorizer converts raw ticket data (JSON dicts or DataFrames) into the feature space
expected by trained models. Preprocessing pipeline is consistent with backend data pipeline.
"""

from typing import Union, Dict, Any, List
import pandas as pd


class TicketVectorizer:
    """
    Vectorizes ticket data into the feature space expected by the model.
    
    Mirrors the preprocessing pipeline from data_preprocessing.py:inference()
    to ensure consistency between training and external XAI inference.
    
    Three usage modes:
    1. Simple mode: transform(text_list) — uses default categorical values
    2. Full ticket mode: transform_full_ticket(dict_or_list_or_df) — all fields vary
    3. Stateful mode: set_base_ticket(ticket) then transform_with_base_ticket(text_list) — categories fixed
    """

    def __init__(
        self,
        one_hot_encoder=None,
        sentence_model_name: str = "all-MiniLM-L6-v2",
        default_category_value: str = "Unknown",
    ):
        """
        Args:
            one_hot_encoder: Fitted OneHotEncoder from sklearn.preprocessing (fitted on training data).
                           Can be None if set later via set_one_hot_encoder() for cloudpickle portability.
            sentence_model_name: Name of the sentence transformer model (default: all-MiniLM-L6-v2)
            default_category_value: Default value for categorical fields in text-only mode (default: "Unknown")
        
        Note: Categorical columns are fixed to ["Service subcategory->Name", "Service->Name"]
              to match the standard preprocessing pipeline.
        """
        self.one_hot_encoder = one_hot_encoder
        self.sentence_model_name = sentence_model_name
        self.default_category_value = default_category_value
        self.cat_cols = ["Service subcategory->Name", "Service->Name"]
        self._sentence_model = None
        self._base_ticket = None

    def set_one_hot_encoder(self, one_hot_encoder):
        """
        Set the one-hot encoder (used when loading with cloudpickle portability).
        
        This allows the vectorizer to be serialized with cloudpickle without the encoder,
        then the encoder is loaded separately and attached before use.
        
        Args:
            one_hot_encoder: Fitted OneHotEncoder from sklearn.preprocessing
        
        Returns:
            self (for chaining if desired)
        """
        self.one_hot_encoder = one_hot_encoder
        return self

    def _get_sentence_model(self):
        """
        Lazily load and cache the sentence transformer model.
        
        Import is done inside the method (not at module level) to avoid including
        sentence_transformers in the module bytecode during cloudpickle serialization.
        This prevents environment-specific module path issues when unpickling across
        different environments (Docker vs local).
        """
        if self._sentence_model is None:
            from sentence_transformers import SentenceTransformer
            self._sentence_model = SentenceTransformer(self.sentence_model_name)
        return self._sentence_model

    def set_base_ticket(self, ticket: Union[Dict[str, Any], pd.Series]) -> None:
        """
        Set the base ticket whose categorical fields will be used for text-only transformations.
        
        This is required before calling transform_with_base_ticket().
        
        Args:
            ticket: Dictionary or pandas Series with ticket fields including:
                   - title_anon
                   - description_anon  
                   - service_subcategory_name
                   - service_name
        
        Raises:
            ValueError: If required fields are missing
        """
        # Convert Series to dict if needed
        if isinstance(ticket, pd.Series):
            ticket = ticket.to_dict()
        
        if not isinstance(ticket, dict):
            raise ValueError("Base ticket must be a dict or pandas Series")
        
        # Validate required fields
        required_fields = ['title_anon', 'description_anon', 'service_subcategory_name', 'service_name']
        missing = [f for f in required_fields if f not in ticket]
        if missing:
            raise ValueError(f"Base ticket missing required fields: {missing}")
        
        self._base_ticket = ticket

    def transform(self, texts: Union[str, List[str]]) -> pd.DataFrame:
        """
        Transform text strings into feature matrix using default categorical values (simple mode).
        
        This is the default/simple mode where only text varies and categorical fields
        are set to the default value (typically "Unknown" for LIME-style explanations).

        Args:
            texts: Single text string or list of text strings to vectorize

        Returns:
            DataFrame with shape (n_samples, n_features)
        """
        # Normalize to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Create ticket dicts with default categorical values
        tickets = [
            {
                'title_anon': text,
                'description_anon': '',
                'service_subcategory_name': self.default_category_value,
                'service_name': self.default_category_value,
            }
            for text in texts
        ]
        
        df = pd.DataFrame(tickets)
        return self._vectorize_dataframe(df)

    def transform_full_ticket(self, df: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        Transform raw ticket data into feature matrix (full ticket mode).
        
        Mimics data_preprocessing.py:inference() to ensure preprocessing consistency.
        All ticket fields (text + categories) are varied.

        Args:
            df: One of:
                - DataFrame with columns: title_anon, description_anon, 
                  service_subcategory_name, service_name
                - Dictionary (single ticket)
                - List of dictionaries (multiple tickets)

        Returns:
            DataFrame with shape (n_samples, n_features) where:
            - First 384 columns: sentence embeddings (all-MiniLM-L6-v2)
            - Remaining columns: one-hot encoded categorical features
        """
        # Convert dict or list of dicts to DataFrame
        if isinstance(df, dict):
            df = pd.DataFrame([df])
        elif isinstance(df, list) and len(df) > 0 and isinstance(df[0], dict):
            df = pd.DataFrame(df)
        
        # Ensure it's a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a DataFrame, dict, or list of dicts")
        
        return self._vectorize_dataframe(df)

    def transform_with_base_ticket(self, texts: Union[str, List[str]]) -> pd.DataFrame:
        """
        Transform perturbed text strings using stored base ticket categories (stateful mode).
        
        Requires set_base_ticket() to be called first.
        
        This method is designed for LIME integration where only text is perturbed
        and categorical fields remain constant from the previously-set base ticket.

        Args:
            texts: Single text string or list of text strings to vectorize

        Returns:
            DataFrame with shape (n_samples, n_features)
        
        Raises:
            RuntimeError: If set_base_ticket() has not been called
        """
        if self._base_ticket is None:
            raise RuntimeError(
                "Base ticket not set. Call set_base_ticket(ticket) before using transform_with_base_ticket()."
            )
        
        # Normalize to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Create ticket dicts combining perturbed text with base ticket's categories
        tickets = [
            {
                'title_anon': text,
                'description_anon': '',
                'service_subcategory_name': self._base_ticket['service_subcategory_name'],
                'service_name': self._base_ticket['service_name'],
            }
            for text in texts
        ]
        
        df = pd.DataFrame(tickets)
        return self._vectorize_dataframe(df)

    def _vectorize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Internal method: vectorize a DataFrame with ticket data.
        
        Args:
            df: DataFrame with ticket fields
        
        Returns:
            Vectorized feature matrix
        
        Raises:
            RuntimeError: If one_hot_encoder has not been set
        """
        if self.one_hot_encoder is None:
            raise RuntimeError(
                "one_hot_encoder not set. Call set_one_hot_encoder(encoder) first, "
                "or load the vectorizer with humal_vectorizer.artifact.load_vectorizer_with_encoder()"
            )
        
        # Make a copy to avoid modifying the input
        df = df.copy()
        
        # Rename columns to match expected names
        df = df.rename(columns={
            'title_anon': 'Title_anon',
            'description_anon': 'Description_anon',
            'service_subcategory_name': 'Service subcategory->Name',
            'service_name': 'Service->Name'
        }, errors='ignore')

        # Create combined title+description column
        df['Title+Description'] = df['Title_anon'] + df['Description_anon']

        # Generate sentence embeddings
        sentence_model = self._get_sentence_model()
        sentences = df['Title+Description'].astype(str).tolist()
        embeddings = sentence_model.encode(sentences, show_progress_bar=False)
        X = pd.DataFrame(embeddings)

        # One-hot encode categorical columns
        one_hot = self.one_hot_encoder.transform(df[self.cat_cols])
        one_hot_df = pd.DataFrame(one_hot.toarray(), index=df.index)

        # Combine embeddings + one-hot features
        X = pd.concat([X, one_hot_df], axis=1)
        X.columns = X.columns.astype(str)

        return X
