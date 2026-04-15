"""
HumAL Vectorizer - Portable TicketVectorizer package.

For external machines loading precompiled vectorizers from MinIO:
    import cloudpickle, joblib
    vectorizer = cloudpickle.load(open('vectorizer.pkl', 'rb'))
    encoder = joblib.load(open('encoder.pkl', 'rb'))
    vectorizer.set_one_hot_encoder(encoder)
"""

from .ticket_vectorizer import TicketVectorizer

__all__ = ["TicketVectorizer"]
