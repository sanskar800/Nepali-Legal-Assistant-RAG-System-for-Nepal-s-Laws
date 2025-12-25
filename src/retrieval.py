"""
Context retrieval module with confidence scoring
Handles hierarchical legal document retrieval from Qdrant
"""
from typing import List, Dict, Any
import numpy as np
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from .config import (
    MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME,
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME, MAX_CONTEXT_CHARS,
    CONSTITUTION_LIMIT, MULUKI_ACT_LIMIT, ACT_LIMIT, RULE_LIMIT,
    MIN_SIMILARITY_SCORE
)
from .utils import logger


class ContextRetrieval:
    """Handles context retrieval with hierarchical legal search"""
    
    def __init__(self):
        """Initialize MongoDB, Qdrant, and embedding model"""
        logger.info("Initializing Context Retrieval...")
        
        # MongoDB setup
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[MONGO_DB_NAME]
        self.meta_col = self.db[MONGO_COLLECTION_NAME]
        
        # Qdrant setup
        self.qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        logger.info("Context Retrieval initialized successfully")
    
    def calculate_confidence_score(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence score based on retrieved documents
        
        Args:
            documents: List of retrieved documents with similarity scores
            
        Returns:
            Confidence score (0-1)
        """
        if not documents:
            return 0.0
        
        # Get similarity scores
        scores = [doc.get("similarity_score", 0.0) for doc in documents]
        
        if not scores:
            return 0.0
        
        # Calculate weighted average (higher weight for top results)
        weights = np.array([1.0 / (i + 1) for i in range(len(scores))])
        weights = weights / weights.sum()
        
        confidence = np.average(scores, weights=weights)
        
        # Penalize if top score is too low
        if scores[0] < MIN_SIMILARITY_SCORE:
            confidence *= 0.5
        
        # Penalize if we have very few results
        if len(documents) < 2:
            confidence *= 0.7
        
        return float(confidence)
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant legal context with hierarchical search
        
        Hierarchy:
        1. Constitution (highest authority)
        2. Muluki Act
        3. Acts
        4. Rules (always appended for procedural guidance)
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            List of documents with metadata and similarity scores
        """
        # Generate query embedding
        query_vec = self.embedding_model.encode("query: " + query).tolist()
        
        final_docs = []
        
        # 1️⃣ Search in hierarchy: Constitution → Muluki Act → Act
        for doc_type, limit in [
            ("constitution", CONSTITUTION_LIMIT),
            ("muluki_act", MULUKI_ACT_LIMIT),
            ("act", ACT_LIMIT)
        ]:
            hits = self.qdrant.query_points(
                collection_name=QDRANT_COLLECTION_NAME,
                query=query_vec,
                limit=limit,
                with_payload=True,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_type",
                            match=MatchValue(value=doc_type)
                        )
                    ]
                )
            )
            
            if hits.points:
                for p in hits.points:
                    # Get metadata from MongoDB
                    meta = self.meta_col.find_one({"qdrant_id": p.id})
                    if meta:
                        # Add similarity score
                        meta["similarity_score"] = p.score
                        final_docs.append(meta)
                
                # Stop at highest authority found
                break
        
        # 2️⃣ ALWAYS append Rules & Regulations (for procedural guidance)
        rule_hits = self.qdrant.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_vec,
            limit=RULE_LIMIT,
            with_payload=True,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value="rule")
                    )
                ]
            )
        )
        
        for p in rule_hits.points:
            meta = self.meta_col.find_one({"qdrant_id": p.id})
            if meta:
                meta["similarity_score"] = p.score
                final_docs.append(meta)
        
        logger.info(f"Retrieved {len(final_docs)} documents for query")
        
        return final_docs
    
    def rerank_by_metadata(self, docs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rerank documents based on metadata matches with query
        
        Args:
            docs: List of documents with metadata
            query: User query
            
        Returns:
            Reranked list of documents
        """
        from .utils import extract_legal_references
        
        # Extract legal references from query
        query_refs = extract_legal_references(query)
        
        # Rerank documents
        for doc in docs:
            boost_factor = 1.0
            
            # Boost if section matches
            doc_section = doc.get("दफा", "")
            if doc_section:
                section_num = doc_section.replace("दफा", "").strip()
                if section_num in query_refs["sections"]:
                    boost_factor *= 1.3  # 30% boost for exact section match
            
            # Boost if chapter matches
            doc_chapter = doc.get("परिच्छेद", "")
            if doc_chapter:
                chapter_num = doc_chapter.replace("परिच्छेद", "").strip()
                if chapter_num in query_refs["chapters"]:
                    boost_factor *= 1.2  # 20% boost for chapter match
            
            # Boost if part matches
            doc_part = doc.get("भाग", "")
            if doc_part:
                part_num = doc_part.replace("भाग", "").strip()
                if part_num in query_refs["parts"]:
                    boost_factor *= 1.15  # 15% boost for part match
            
            # Boost based on document priority (Constitution > Muluki > Act > Rule)
            priority = doc.get("priority", 4)
            if priority == 1:  # Constitution
                boost_factor *= 1.1
            elif priority == 2:  # Muluki Act
                boost_factor *= 1.05
            
            # Apply boost to similarity score
            doc["similarity_score"] = doc.get("similarity_score", 0.0) * boost_factor
            doc["metadata_boost"] = boost_factor
        
        # Sort by boosted similarity score
        reranked = sorted(docs, key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        
        logger.info(f"Reranked {len(docs)} documents using metadata")
        
        return reranked
    
    def build_context(self, docs: List[Dict[str, Any]], max_chars: int = MAX_CONTEXT_CHARS) -> str:
        """
        Build compact legal context from documents
        
        Args:
            docs: List of documents
            max_chars: Maximum characters for context
            
        Returns:
            Formatted context string
        """
        context_blocks = []
        total_chars = 0
        
        for d in docs:
            # Build header with legal structure
            header = (
                f"Law Type: {d['doc_type']}\n"
                f"{d.get('भाग', '')} {d.get('परिच्छेद', '')} "
                f"{d.get('दफा', '')} {d.get('उपदफा', '')}\n"
            )
            
            body = d["text"]
            block = header + body + "\n\n"
            
            # Check if adding this block exceeds limit
            if total_chars + len(block) > max_chars:
                break
            
            context_blocks.append(block)
            total_chars += len(block)
        
        return "".join(context_blocks)
    
    def filter_by_confidence(
        self,
        documents: List[Dict[str, Any]],
        min_score: float = MIN_SIMILARITY_SCORE
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by minimum similarity score
        
        Args:
            documents: List of documents
            min_score: Minimum similarity score
            
        Returns:
            Filtered list of documents
        """
        filtered = [
            doc for doc in documents
            if doc.get("similarity_score", 0.0) >= min_score
        ]
        
        logger.info(f"Filtered {len(documents)} -> {len(filtered)} documents (min_score={min_score})")
        
        return filtered
