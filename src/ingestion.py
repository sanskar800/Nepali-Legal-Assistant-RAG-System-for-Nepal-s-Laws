"""
Document ingestion module for Nepali Law Bot
Handles PDF extraction, chunking, and storage in MongoDB + Qdrant
"""
import os
import re
import uuid
from typing import Dict, List, Tuple
import pdfplumber
from tqdm import tqdm
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

from .config import (
    MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME,
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME,
    VECTOR_SIZE, EMBEDDING_MODEL_NAME, CHUNK_MIN_LENGTH
)
from .utils import logger


class DocumentIngestion:
    """Handles document ingestion pipeline"""
    
    def __init__(self):
        """Initialize MongoDB, Qdrant, and embedding model"""
        logger.info("Initializing Document Ingestion...")
        
        # MongoDB setup
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[MONGO_DB_NAME]
        self.meta_col = self.db[MONGO_COLLECTION_NAME]
        
        # Create unique index to prevent duplicates
        self.meta_col.create_index("qdrant_id", unique=True)
        logger.info(f"Connected to MongoDB: {MONGO_DB_NAME}")
        
        # Qdrant setup
        self.qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Create collection if not exists
        collections = [c.name for c in self.qdrant.get_collections().collections]
        if QDRANT_COLLECTION_NAME not in collections:
            self.qdrant.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION_NAME}")
        else:
            logger.info(f"Using existing Qdrant collection: {QDRANT_COLLECTION_NAME}")
        
        # Load embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Document Ingestion initialized successfully")
    
    @staticmethod
    def detect_doc_type(path: str) -> Tuple[str, int]:
        """
        Detect document type and priority from file path
        
        Args:
            path: File path
            
        Returns:
            Tuple of (doc_type, priority)
        """
        p = path.lower()
        if "संविधान" in p:
            return "constitution", 1
        if "मुलुकी" in p:
            return "muluki_act", 2
        if "नियम" in p or "विनियम" in p:
            return "rule", 4
        return "act", 3
    
    @staticmethod
    def extract_structure(text: str) -> Dict[str, str]:
        """
        Extract Nepali legal structure from text
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with भाग, परिच्छेद, दफा, उपदफा
        """
        structure = {
            "भाग": None,
            "भाग_title": None,
            "परिच्छेद": None,
            "परिच्छेद_title": None,
            "दफा": None,
            "उपदफा": None
        }
        
        # Extract Part (भाग)
        part = re.search(r"(भाग–?\s*\d+)\s*(.*)", text)
        if part:
            structure["भाग"] = part.group(1)
            structure["भाग_title"] = part.group(2)
        
        # Extract Chapter (परिच्छेद)
        pariched = re.search(r"(परिच्छेद–?\s*\d+)\s*(.*)", text)
        if pariched:
            structure["परिच्छेद"] = pariched.group(1)
            structure["परिच्छेद_title"] = pariched.group(2)
        
        # Extract Section (दफा)
        dafa = re.search(r"(दफा\s*\d+)", text)
        if dafa:
            structure["दफा"] = dafa.group(1)
        
        # Extract Sub-section (उपदफा)
        up = re.search(r"(\(\d+\))", text)
        if up:
            structure["उपदफा"] = up.group(1)
        
        return structure
    
    @staticmethod
    def chunk_text(text: str) -> List[str]:
        """
        Split text into chunks by section (दफा)
        
        Args:
            text: Full document text
            
        Returns:
            List of text chunks
        """
        chunks = re.split(r"\n(?=दफा\s*\d+)", text)
        return [c.strip() for c in chunks if len(c.strip()) > CHUNK_MIN_LENGTH]
    
    def ingest_documents(self, base_dir: str) -> None:
        """
        Ingest all PDF documents from directory
        
        Args:
            base_dir: Base directory containing PDF files
        """
        # Find all PDF files
        pdf_files = []
        for root, _, files in os.walk(base_dir):
            for f in files:
                if f.endswith(".pdf"):
                    pdf_files.append(os.path.join(root, f))
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc="Ingesting documents"):
            doc_type, priority = self.detect_doc_type(pdf_path)
            
            # Extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
            
            # Chunk the text
            chunks = self.chunk_text(full_text)
            
            # Process each chunk
            for chunk in chunks:
                structure = self.extract_structure(chunk)
                
                # Check if chunk already exists (prevent duplicates)
                exists = self.meta_col.find_one({
                    "text": chunk,
                    "doc_type": doc_type
                })
                if exists:
                    continue
                
                # Generate unique ID
                qdrant_id = str(uuid.uuid4())
                
                # Create embedding
                embedding = self.embedding_model.encode(
                    "passage: " + chunk
                ).tolist()
                
                # Store in Qdrant
                self.qdrant.upsert(
                    collection_name=QDRANT_COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=qdrant_id,
                            vector=embedding,
                            payload={"doc_type": doc_type}
                        )
                    ]
                )
                
                # Store metadata in MongoDB
                self.meta_col.insert_one({
                    "qdrant_id": qdrant_id,
                    "doc_type": doc_type,
                    "priority": priority,
                    "file_path": pdf_path,
                    **structure,
                    "text": chunk
                })
        
        logger.info("Document ingestion completed")


if __name__ == "__main__":
    # Example usage
    ingestion = DocumentIngestion()
    
    # Get docs directory from environment or use default
    docs_dir = os.getenv("DOCS_DIR", "./docs")
    
    if os.path.exists(docs_dir):
        ingestion.ingest_documents(docs_dir)
    else:
        logger.error(f"Documents directory not found: {docs_dir}")
        logger.info("Please set DOCS_DIR environment variable or create ./docs directory")
