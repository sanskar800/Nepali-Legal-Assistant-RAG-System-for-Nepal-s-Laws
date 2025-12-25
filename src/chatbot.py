"""
Main chatbot module for Nepali Law Bot
Integrates retrieval, LLM generation, and output parsing
"""
# Suppress verbose logging first
from . import suppress_logs

from typing import Optional
from langdetect import detect, LangDetectException
from groq import Groq

from .retrieval import ContextRetrieval
from .output_parser import OutputParser, LegalResponse
from .config import (
    GROQ_API_KEY, GROQ_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS,
    SYSTEM_PROMPT_EN, SYSTEM_PROMPT_NE,
    CONFIDENCE_THRESHOLD
)
from .utils import logger


class NepaliLawBot:
    """Main chatbot class for Nepali legal queries"""
    
    def __init__(self):
        """Initialize chatbot components"""
        logger.info("Initializing Nepali Law Bot...")
        
        # Initialize retrieval
        self.retrieval = ContextRetrieval()
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        
        # Initialize output parser
        self.parser = OutputParser()
        
        logger.info("Nepali Law Bot initialized successfully")
    
    def decide_language(self, query: str) -> str:
        """
        Detect query language
        
        Args:
            query: User query
            
        Returns:
            Language code ('en' or 'ne')
        """
        try:
            # Detect language using langdetect
            lang = detect(query)
            
            # Map to our supported languages
            if lang == "ne":
                return "ne"
            else:
                return "en"
        except LangDetectException:
            # Default to English if detection fails
            return "en"
    
    def generate_answer(self, query: str, context: str, language: str) -> str:
        """
        Generate answer using Groq LLM
        
        Args:
            query: User query
            context: Retrieved context
            language: Response language
            
        Returns:
            Generated answer
        """
        # Select system prompt based on language
        system_prompt = SYSTEM_PROMPT_NE if language == "ne" else SYSTEM_PROMPT_EN
        
        # Add explicit language instruction to user message
        if language == "en":
            language_instruction = "\n\nIMPORTANT: Please respond in ENGLISH only, even though the legal documents above are in Nepali. Translate and explain the provisions in English."
        else:
            language_instruction = "\n\nमहत्वपूर्ण: कृपया नेपालीमा मात्र जवाफ दिनुहोस्।"
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{query}{language_instruction}"
            }
        ]
        
        # Generate response
        logger.info(f"Generating answer with {GROQ_MODEL}")
        completion = self.groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
        
        return completion.choices[0].message.content
    
    def query(self, user_query: str, return_raw: bool = False) -> LegalResponse:
        """
        Process user query and return structured response
        
        Args:
            user_query: User's legal query
            return_raw: If True, return raw dict instead of LegalResponse
            
        Returns:
            LegalResponse object with answer, citations, and confidence
        """
        logger.info(f"Processing query: {user_query[:100]}...")
        
        # Detect language
        language = self.decide_language(user_query)
        logger.info(f"Detected language: {language}")
        
        # Retrieve relevant documents
        documents = self.retrieval.retrieve_context(user_query)
        
        # Rerank using metadata
        documents = self.retrieval.rerank_by_metadata(documents, user_query)
        
        # Calculate confidence score
        confidence_score = self.retrieval.calculate_confidence_score(documents)
        logger.info(f"Confidence score: {confidence_score:.2f}")
        
        # Filter low-confidence documents
        filtered_docs = self.retrieval.filter_by_confidence(documents)
        
        # Build context
        context = self.retrieval.build_context(filtered_docs)
        
        # Generate answer
        answer = self.generate_answer(user_query, context, language)
        
        # Create structured response
        response = self.parser.create_response(
            answer=answer,
            confidence_score=confidence_score,
            language=language,
            sources=filtered_docs,
            confidence_threshold=CONFIDENCE_THRESHOLD
        )
        
        logger.info("Query processed successfully")
        
        return response
    
    def chat(self) -> None:
        """
        Interactive chat loop
        """
        print("\n" + "=" * 80)
        print("🏛️  NEPALI LAW BOT - Legal Assistant for Nepali Law")
        print("=" * 80)
        print("\nType your legal question in English or Nepali.")
        print("Type 'quit' or 'exit' to end the session.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n👋 Thank you for using Nepali Law Bot. Goodbye!\n")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Process query
                print("\n🔍 Searching legal documents...")
                response = self.query(user_input)
                
                # Display formatted response
                print("\n" + response.format_for_display())
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"\n❌ Error: {e}")
                print("Please try again with a different query.\n")


if __name__ == "__main__":
    # Run interactive chat
    bot = NepaliLawBot()
    bot.chat()
