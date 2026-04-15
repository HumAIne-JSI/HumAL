"""
Ticket Vectorizer Service - manages serialization and loading of TicketVectorizer for XAI integration.

The TicketVectorizer is now a standalone module (humal_vectorizer) to enable
portability—it can be loaded on external machines without the full app context.

This service wraps TicketVectorizer for backend use and MinIO persistence.
Preprocessing pipeline is consistent with backend/app/services/data_preprocessing.py:inference()
"""

from humal_vectorizer import TicketVectorizer


class TicketVectorizerService:
    """High-level service for managing TicketVectorizer lifecycle and MinIO persistence.
    
    Supports three transformation modes:
    - transform(texts): Simple mode using default categorical values (typically "Unknown")
    - transform_full_ticket(ticket_data): Full mode where all fields vary
    - transform_with_base_ticket(texts): Stateful mode with fixed categories from base ticket
    """

    def __init__(self, minio_service):
        """
        Args:
            minio_service: MinioService instance for persisting vectorizers
        """
        self.minio_service = minio_service

    def create_vectorizer(
        self,
        one_hot_encoder=None,
        sentence_model_name: str = "all-MiniLM-L6-v2",
        default_category_value: str = "Unknown",
    ) -> TicketVectorizer:
        """
        Create a TicketVectorizer instance with an optional OneHotEncoder.

        Note: The base ticket is NOT baked into the vectorizer and must be set
        by the consumer via set_base_ticket() before using transform_with_base_ticket().

        Args:
            one_hot_encoder: OneHotEncoder fitted on training data (optional, defaults to None)
            sentence_model_name: Sentence transformer model name (default: all-MiniLM-L6-v2)
            default_category_value: Default categorical value for simple text-only mode (default: "Unknown")

        Returns:
            TicketVectorizer instance ready for use or serialization
        """
        return TicketVectorizer(
            one_hot_encoder=one_hot_encoder,
            sentence_model_name=sentence_model_name,
            default_category_value=default_category_value,
        )

    def save_vectorizer(
        self,
        *,
        al_instance_id: int,
        vectorizer: TicketVectorizer,
    ):
        """
        Persist a TicketVectorizer to MinIO (WITHOUT encoder).

        The vectorizer is saved standalone (one_hot_encoder=None) for portability.
        The encoder is saved separately during model training and loaded independently
        when deserializing.

        Args:
            al_instance_id: Active Learning instance ID
            vectorizer: TicketVectorizer instance to save (encoder will be removed if present)

        Returns:
            Dictionary with bucket, object path, and metadata
        """
        # Save encoder temporarily if it exists, and remove from vectorizer
        encoder = vectorizer.one_hot_encoder
        vectorizer.one_hot_encoder = None
        try:
            vectorizer_metadata = self.minio_service.save_ticket_vectorizer(
                al_instance_id=al_instance_id,
                vectorizer=vectorizer,
            )
        finally:
            # Restore encoder to original instance if it existed
            if encoder is not None:
                vectorizer.one_hot_encoder = encoder
        
        return vectorizer_metadata

    def load_vectorizer(
        self,
        *,
        al_instance_id: int,
    ) -> TicketVectorizer:
        """
        Load a TicketVectorizer from MinIO with its encoder attached.

        The vectorizer and encoder are stored separately in MinIO.
        This method loads both and attaches the encoder to the vectorizer.

        Args:
            al_instance_id: Active Learning instance ID

        Returns:
            TicketVectorizer instance with encoder attached, ready for inference
        """
        # Load vectorizer (will have encoder=None)
        vectorizer = self.minio_service.load_ticket_vectorizer(
            al_instance_id=al_instance_id,
        )
        
        # Load and attach encoder
        encoder = self.minio_service.load_one_hot_encoder(
            al_instance_id=al_instance_id,
        )
        vectorizer.set_one_hot_encoder(encoder)
        
        return vectorizer
