# Quick Start Guide

## Setup (One-time)

1. **Open PowerShell in project directory**
   ```powershell
   cd "c:\Users\NITRO\OneDrive\Documents\rag projects\nepali-law-bot"
   ```

2. **Run setup script**
   ```powershell
   .\setup_venv.bat
   ```

3. **Activate virtual environment**
   ```powershell
   venv\Scripts\activate
   ```

## Usage

### Interactive Chat
```powershell
python main.py
```

### Run Examples
```powershell
python examples\query_bot.py
```

### Test Confidence Scoring
```powershell
python examples\test_confidence.py
```

## Example Queries

**English:**
- "How can I get a divorce in Nepal?"
- "What are the property rights of women?"
- "What is the legal age for marriage?"

**Nepali:**
- "नेपालमा सम्पत्ति कसरी बाँड्ने?"
- "विवाह विच्छेदका आधारहरू के हुन्?"

## Troubleshooting

### Import Errors
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration Errors
Ensure `.env` contains all required variables:
- MONGO_URI
- QDRANT_URL
- QDRANT_API_KEY
- GROQ_API_KEY
- DRIVE_LINK

## Features

✅ Confidence scoring (detects hallucinations)  
✅ Structured output with legal citations  
✅ Bilingual (English & Nepali)  
✅ Hierarchical legal retrieval  
✅ Source document tracking  
✅ Clean output (verbose logs suppressed)
