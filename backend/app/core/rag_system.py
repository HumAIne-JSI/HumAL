"""
RAG System for ticket resolution using FAISS and Sentence Transformers.
"""
import pandas as pd
import numpy as np
import re
import os
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.config.resolution_config import EMBEDDING_CACHE_DIR

# Cache for RAG system
_RAG_CACHE = {"kb_path": None, "kb_mtime": None, "rag": None, "df": None}

# Load the knowledge base
def load_knowledge_base(file_path):
    """Function that loads the knowledge base from a file_path and extracts the first replies."""
    df = pd.read_csv(file_path)
    df = df.dropna(subset=['Public_log_anon'])  # Drop rows without public logs

    df['first_reply'] = df['Public_log_anon'].apply(_extract_first_reply)
    df = df.dropna(subset=['first_reply'])  # Drop rows without first replies

    return df

def _extract_first_reply(text):
    """Function that extracts the first reply from the text."""
    if pd.isna(text):
        return None
    
    text_str = str(text)
    
    # More aggressive pattern to find timestamp separators and user info
    timestamp_pattern = r'\*{10,}\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
    
    # Also look for patterns like ": servicedesk (0) ************" or ": Name (ID) ************"
    user_pattern = r':\s*[^(]*\([^)]*\)\s*\*{10,}'
    
    # Split by timestamp pattern first
    parts = re.split(timestamp_pattern, text_str)
    
    if len(parts) >= 2:
        first_reply = parts[1].strip()
        
        # Remove user info pattern at the beginning
        first_reply = re.sub(user_pattern, '', first_reply, flags=re.IGNORECASE).strip()
        
        # Find the next timestamp to cut off subsequent replies
        next_timestamp_match = re.search(timestamp_pattern, first_reply)
        if next_timestamp_match:
            first_reply = first_reply[:next_timestamp_match.start()].strip()
        
        # Find next user pattern to cut off subsequent replies
        next_user_match = re.search(user_pattern, first_reply)
        if next_user_match:
            first_reply = first_reply[:next_user_match.start()].strip()
        
        # Clean up common artifacts
        first_reply = re.sub(r'^-+\s*', '', first_reply)  # Remove leading dashes
        first_reply = re.sub(r'\s*-+$', '', first_reply)  # Remove trailing dashes
        first_reply = re.sub(r'^\s*Dear\s+[^,]+,?\s*', '', first_reply, flags=re.IGNORECASE)  # Remove "Dear Name," at start
        
        # Remove lines that are just separators or user info
        lines = first_reply.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are just separators or user info
            if not re.match(r'^-{5,}$', line) and not re.match(r'^\s*:\s*[^(]*\([^)]*\)', line):
                cleaned_lines.append(line)
        
        first_reply = '\n'.join(cleaned_lines).strip()
        
        # Return only if it's substantial (not just whitespace or artifacts)
        return first_reply if len(first_reply) > 50 else None
    
    return text_str[:500] if len(text_str) > 50 else None


class RAGSystem:
    def __init__(self, knowledge_base, sentence_model_name="all-MiniLM-L6-v2", kb_path: str | None = None):
        self.knowledge_base = knowledge_base
        self.sentence_model_name = sentence_model_name
        self.sentence_model = SentenceTransformer(sentence_model_name)
        self.index = None
        self.embeddings = None
        self.title_embeddings = None
        self.description_embeddings = None
        self.category_index = {}
        self.kb_path = kb_path

    def build_index(self, kb_path: str | None = None, kb_mtime: float | None = None):
        """Build or load cached embeddings + FAISS index.

        Caching strategy:
        - Cache file stored under embeddings_cache/<basename>_<model>_<mtime>.npz
        - If cache exists, load arrays and rebuild FAISS index (fast)
        - If DISABLE_EMBEDDING_CACHE env var is set to '1', force rebuild
        """
        if self.index is not None and self.embeddings is not None:
            return  # Already built in-memory

        kb_path = kb_path or self.kb_path
        cache_disabled = os.getenv("DISABLE_EMBEDDING_CACHE") == "1"
        os.makedirs(EMBEDDING_CACHE_DIR, exist_ok=True)
        cache_file = None
        if kb_path and kb_mtime:
            safe_model = self.sentence_model_name.replace('/', '_')
            cache_key = f"{os.path.basename(kb_path)}_{safe_model}_{int(kb_mtime)}"
            cache_file = os.path.join(EMBEDDING_CACHE_DIR, f"{cache_key}.npz")

        # Try loading cache
        if cache_file and not cache_disabled and os.path.exists(cache_file):
            try:
                data = np.load(cache_file, allow_pickle=False)
                self.title_embeddings = data['title_embeddings']
                self.description_embeddings = data['description_embeddings']
                self.embeddings = data['embeddings']
                # Rebuild FAISS index
                self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
                faiss.normalize_L2(self.embeddings)
                self.index.add(self.embeddings)
                self._build_category_index()
                print(f"⚡ Loaded embeddings cache from {cache_file}")
                return
            except Exception as e:
                print(f"⚠️ Failed to load embedding cache ({e}), rebuilding...")

        # Build fresh embeddings
        titles = self.knowledge_base['Title_anon'].fillna('').tolist()
        descriptions = self.knowledge_base['Description_anon'].fillna('').tolist()
        print("🔄 Building embeddings (no valid cache)...")
        self.title_embeddings = self.sentence_model.encode(titles, show_progress_bar=True)
        self.description_embeddings = self.sentence_model.encode(descriptions, show_progress_bar=True)
        texts = [f"{title} {desc}".strip() for title, desc in zip(titles, descriptions)]
        self.embeddings = self.sentence_model.encode(texts, show_progress_bar=True)
        self.embeddings = np.array(self.embeddings).astype('float32')
        faiss.normalize_L2(self.embeddings)
        self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)
        self._build_category_index()
        print("✅ Enhanced index built successfully")

        # Persist cache
        if cache_file and not cache_disabled:
            try:
                np.savez_compressed(
                    cache_file,
                    title_embeddings=self.title_embeddings,
                    description_embeddings=self.description_embeddings,
                    embeddings=self.embeddings,
                )
                print(f"💾 Saved embeddings cache to {cache_file}")
            except Exception as e:
                print(f"⚠️ Failed to save embeddings cache: {e}")

    def _build_category_index(self):
        """Build index by categories for faster filtering"""
        if 'label_auto' in self.knowledge_base.columns:
            for category in self.knowledge_base['label_auto'].unique():
                if pd.notna(category):
                    mask = self.knowledge_base['label_auto'] == category
                    self.category_index[category] = self.knowledge_base[mask].index.tolist()

    def retrieve_similar_replies(self, query, top_k=5, predicted_category=None):
        """Enhanced retrieval with multi-factor scoring and category awareness"""
        
        # Get larger candidate set for re-ranking
        search_k = min(top_k * 4, len(self.knowledge_base))
        
        # Step 1: Get candidates from FAISS
        query_embedding = self.sentence_model.encode([query])
        faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), search_k)
        
        candidates = self.knowledge_base.iloc[indices[0]].copy()
        candidates['faiss_score'] = distances[0]
        
        # Step 2: Calculate enhanced scores
        enhanced_scores = []
        for idx, row in candidates.iterrows():
            score = self._calculate_enhanced_score(query, row, predicted_category, distances[0][candidates.index.get_loc(idx)])
            enhanced_scores.append(score)
        
        candidates['enhanced_score'] = enhanced_scores
        
        # Step 3: Re-rank and return top results
        results = candidates.nlargest(top_k, 'enhanced_score')
        return results[['first_reply', 'Title_anon', 'Description_anon', 'enhanced_score']]

    def _calculate_enhanced_score(self, query, candidate_row, predicted_category, faiss_score):
        """Calculate enhanced score considering multiple factors"""
        # Base FAISS similarity (50%)
        base_score = 0.5 * faiss_score
        
        # Category match bonus (20%)
        category_bonus = 0.0
        if predicted_category and candidate_row.get('label_auto') == predicted_category:
            category_bonus = 0.2
        
        # Title similarity (15%)
        title_sim = self._calculate_field_similarity(query, candidate_row.get('Title_anon', ''))
        title_score = 0.15 * title_sim
        
        # Description similarity (10%)
        desc_sim = self._calculate_field_similarity(query, candidate_row.get('Description_anon', ''))
        desc_score = 0.1 * desc_sim
        
        # Response quality bonus (5%)
        quality_bonus = 0.05 * self._assess_response_quality(candidate_row.get('first_reply', ''))
        
        return base_score + category_bonus + title_score + desc_score + quality_bonus

    def _calculate_field_similarity(self, query, field_text):
        """Calculate similarity between query and specific field"""
        if pd.isna(field_text) or not str(field_text).strip():
            return 0.0
        
        try:
            query_emb = self.sentence_model.encode([query])
            field_emb = self.sentence_model.encode([str(field_text)])
            similarity = cosine_similarity(query_emb, field_emb)[0][0]
            return max(0.0, similarity)
        except:
            return 0.0

    def _assess_response_quality(self, response_text):
        """Assess response quality for scoring"""
        if pd.isna(response_text) or not str(response_text).strip():
            return 0.0
        
        response_str = str(response_text)
        quality_score = 0.0
        
        # Length check (not too short, not too long)
        length = len(response_str)
        if 50 <= length <= 2000:
            quality_score += 0.4
        
        # Has professional structure
        if any(greeting in response_str.lower() for greeting in ['dear', 'hello', 'thank you', 'need:']):
            quality_score += 0.3
        
        # Contains useful information
        if any(info in response_str.lower() for info in ['information', 'required', 'approval', 'project', 'manager']):
            quality_score += 0.3
        
        return min(1.0, quality_score)