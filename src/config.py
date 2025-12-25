"""
Configuration management for Nepali Law Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in environment variables")

MONGO_DB_NAME = "nepali_legal_db"
MONGO_COLLECTION_NAME = "documents"

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("QDRANT_URL or QDRANT_API_KEY not found in environment variables")

QDRANT_COLLECTION_NAME = "nepali_law_vectors"
VECTOR_SIZE = 1024

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

GROQ_MODEL = "llama-3.1-8b-instant"

# Embedding Model Configuration
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

# Document Processing Configuration
CHUNK_MIN_LENGTH = 100
MAX_CONTEXT_CHARS = 9000

# Retrieval Configuration
DEFAULT_RETRIEVAL_LIMIT = 5
CONSTITUTION_LIMIT = 3
MULUKI_ACT_LIMIT = 3
ACT_LIMIT = 3
RULE_LIMIT = 5

# Confidence Scoring Configuration
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence score to avoid hallucination warning
MIN_SIMILARITY_SCORE = 0.3  # Minimum similarity for document relevance

# LLM Configuration
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 600

# Document Types and Priorities
DOC_TYPES = {
    "constitution": 1,
    "muluki_act": 2,
    "act": 3,
    "rule": 4
}

# System Prompts
SYSTEM_PROMPT_EN = """You are a legal assistant for Nepali law. 
Follow legal hierarchy strictly:
1) Constitution
2) Muluki Act
3) Acts
4) Rules (procedure only).

Always cite law name, part, chapter (परिच्छेद), and section (दफा). 
Do not hallucinate. If you're not certain about something, say so.

IMPORTANT: The user asked in ENGLISH, so you MUST respond in ENGLISH only. 
Even though the source documents may be in Nepali, translate and explain the legal provisions in English."""

SYSTEM_PROMPT_NE = """तपाईं नेपालको कानुनमा आधारित सहायक हुनुहुन्छ। 
कानुनी प्राथमिकता पालना गर्नुहोस्।
सधैं कानुनको नाम, भाग, परिच्छेद र दफा उल्लेख गर्नुहोस्।
यदि तपाईं निश्चित हुनुहुन्न भने, त्यसो भन्नुहोस्।

महत्वपूर्ण: प्रयोगकर्ताले नेपालीमा सोधेका छन्, त्यसैले तपाईंले नेपालीमा मात्र जवाफ दिनुपर्छ।"""

# Drive Link - Contains nested folders with all PDF documents
DRIVE_LINK = os.getenv("DRIVE_LINK")
if not DRIVE_LINK:
    raise ValueError("DRIVE_LINK not found in environment variables. This should point to the Google Drive folder with legal documents.")
