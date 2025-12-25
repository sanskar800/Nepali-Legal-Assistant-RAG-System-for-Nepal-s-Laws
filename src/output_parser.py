"""
Output parser for structured legal responses
Uses Pydantic models for validation and formatting
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import re


class LegalCitation(BaseModel):
    """Model for a legal citation"""
    law_name: Optional[str] = Field(None, description="Name of the law")
    doc_type: Optional[str] = Field(None, description="Type of document (constitution, act, etc.)")
    part: Optional[str] = Field(None, description="Part (भाग)")
    chapter: Optional[str] = Field(None, description="Chapter (परिच्छेद)")
    section: Optional[str] = Field(None, description="Section (दफा)")
    subsection: Optional[str] = Field(None, description="Subsection (उपदफा)")


class SourceDocument(BaseModel):
    """Model for a source document"""
    doc_type: str = Field(..., description="Document type")
    text_preview: str = Field(..., description="Preview of the text")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    structure: Dict[str, Optional[str]] = Field(default_factory=dict, description="Legal structure")


class LegalResponse(BaseModel):
    """Structured legal response model"""
    answer: str = Field(..., description="Main answer text")
    citations: List[LegalCitation] = Field(default_factory=list, description="Legal citations found")
    confidence_score: float = Field(..., description="Overall confidence score (0-1)")
    language: str = Field(..., description="Response language (en/ne)")
    sources: List[SourceDocument] = Field(default_factory=list, description="Source documents")
    warning: Optional[str] = Field(None, description="Warning message if confidence is low")
    
    def format_for_display(self) -> str:
        """
        Format response for console display
        
        Returns:
            Formatted string for display
        """
        output = []
        
        # Header
        output.append("=" * 80)
        output.append("LEGAL RESPONSE")
        output.append("=" * 80)
        
        # Warning if low confidence
        if self.warning:
            output.append(f"\n⚠️  WARNING: {self.warning}\n")
        
        # Answer
        output.append("\n📝 ANSWER:")
        output.append("-" * 80)
        output.append(self.answer)
        output.append("")
        
        # Confidence
        confidence_pct = self.confidence_score * 100
        confidence_bar = "█" * int(confidence_pct / 5) + "░" * (20 - int(confidence_pct / 5))
        output.append(f"📊 CONFIDENCE: {confidence_bar} {confidence_pct:.1f}%")
        output.append("")
        
        # Citations
        if self.citations:
            output.append("📚 LEGAL CITATIONS:")
            output.append("-" * 80)
            for i, citation in enumerate(self.citations, 1):
                parts = []
                if citation.law_name:
                    parts.append(f"Law: {citation.law_name}")
                if citation.part:
                    parts.append(f"Part: {citation.part}")
                if citation.chapter:
                    parts.append(f"Chapter: {citation.chapter}")
                if citation.section:
                    parts.append(f"Section: {citation.section}")
                if citation.subsection:
                    parts.append(f"Subsection: {citation.subsection}")
                
                output.append(f"  {i}. {' | '.join(parts)}")
            output.append("")
        
        # Sources
        if self.sources:
            output.append("📖 SOURCES:")
            output.append("-" * 80)
            for i, source in enumerate(self.sources, 1):
                score_pct = source.similarity_score * 100
                output.append(f"  {i}. [{source.doc_type.upper()}] Relevance: {score_pct:.1f}%")
                
                # Show structure if available
                structure_parts = []
                for key, value in source.structure.items():
                    if value:
                        structure_parts.append(f"{key}: {value}")
                if structure_parts:
                    output.append(f"     {' | '.join(structure_parts)}")
                
                # Show text preview
                preview = source.text_preview[:150] + "..." if len(source.text_preview) > 150 else source.text_preview
                output.append(f"     Preview: {preview}")
                output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)


class OutputParser:
    """Parser for extracting structured information from responses"""
    
    @staticmethod
    def extract_citations(text: str) -> List[LegalCitation]:
        """
        Extract legal citations from text
        
        Args:
            text: Response text
            
        Returns:
            List of LegalCitation objects
        """
        citations = []
        
        # Pattern for Nepali legal references
        # Example: "दफा 17", "परिच्छेद 9", "भाग 3"
        
        # Extract sections (दफा)
        sections = re.findall(r"दफा\s*(\d+)", text)
        for section in sections:
            citations.append(LegalCitation(section=f"दफा {section}"))
        
        # Extract chapters (परिच्छेद)
        chapters = re.findall(r"परिच्छेद\s*(\d+)", text)
        for chapter in chapters:
            citations.append(LegalCitation(chapter=f"परिच्छेद {chapter}"))
        
        # Extract parts (भाग)
        parts = re.findall(r"भाग\s*(\d+)", text)
        for part in parts:
            citations.append(LegalCitation(part=f"भाग {part}"))
        
        return citations
    
    @staticmethod
    def create_response(
        answer: str,
        confidence_score: float,
        language: str,
        sources: List[Dict[str, Any]],
        confidence_threshold: float = 0.5
    ) -> LegalResponse:
        """
        Create a structured legal response
        
        Args:
            answer: Answer text from LLM
            confidence_score: Confidence score (0-1)
            language: Response language
            sources: List of source documents
            confidence_threshold: Threshold for low confidence warning
            
        Returns:
            LegalResponse object
        """
        # Extract citations from answer
        citations = OutputParser.extract_citations(answer)
        
        # Create source documents
        source_docs = []
        for src in sources:
            source_docs.append(SourceDocument(
                doc_type=src.get("doc_type", "unknown"),
                text_preview=src.get("text", "")[:200],
                similarity_score=src.get("similarity_score", 0.0),
                structure={
                    "भाग": src.get("भाग"),
                    "परिच्छेद": src.get("परिच्छेद"),
                    "दफा": src.get("दफा"),
                    "उपदफा": src.get("उपदफा")
                }
            ))
        
        # Add warning if confidence is low
        warning = None
        if confidence_score < confidence_threshold:
            if language == "ne":
                warning = "यो जवाफको विश्वसनीयता कम छ। कृपया कानुनी विशेषज्ञसँग परामर्श गर्नुहोस्।"
            else:
                warning = "This response has low confidence. Please consult with a legal expert."
        
        return LegalResponse(
            answer=answer,
            citations=citations,
            confidence_score=confidence_score,
            language=language,
            sources=source_docs,
            warning=warning
        )
