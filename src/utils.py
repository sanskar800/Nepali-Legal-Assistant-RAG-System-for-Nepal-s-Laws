"""
Utility functions for Nepali Law Bot
"""
import logging
from typing import Optional
from colorama import Fore, Style, init

# Initialize colorama for Windows
init(autoreset=True)

def setup_logging(level: int = logging.WARNING) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        level: Logging level (default: WARNING to reduce verbosity)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger("nepali_law_bot")

def print_colored(text: str, color: str = "white") -> None:
    """
    Print colored text to console
    
    Args:
        text: Text to print
        color: Color name (red, green, yellow, blue, magenta, cyan, white)
    """
    color_map = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE
    }
    
    print(f"{color_map.get(color, Fore.WHITE)}{text}{Style.RESET_ALL}")

def format_confidence(score: float) -> str:
    """
    Format confidence score with color coding
    
    Args:
        score: Confidence score (0-1)
        
    Returns:
        Formatted string with color
    """
    percentage = score * 100
    
    if score >= 0.7:
        color = Fore.GREEN
        label = "High"
    elif score >= 0.5:
        color = Fore.YELLOW
        label = "Medium"
    else:
        color = Fore.RED
        label = "Low"
    
    return f"{color}{label} ({percentage:.1f}%){Style.RESET_ALL}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_legal_references(text: str) -> dict:
    """
    Extract legal references from text (section numbers, chapters, parts)
    
    Args:
        text: Text to extract references from
        
    Returns:
        Dictionary with extracted references
    """
    import re
    
    references = {
        "sections": [],      # दफा
        "chapters": [],      # परिच्छेद
        "parts": [],         # भाग
        "subsections": []    # उपदफा
    }
    
    # Extract sections (दफा)
    section_patterns = [
        r"दफा\s*(\d+)",
        r"section\s*(\d+)",
        r"धारा\s*(\d+)"
    ]
    for pattern in section_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references["sections"].extend(matches)
    
    # Extract chapters (परिच्छेद)
    chapter_patterns = [
        r"परिच्छेद\s*(\d+)",
        r"chapter\s*(\d+)"
    ]
    for pattern in chapter_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references["chapters"].extend(matches)
    
    # Extract parts (भाग)
    part_patterns = [
        r"भाग\s*(\d+)",
        r"part\s*(\d+)"
    ]
    for pattern in part_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references["parts"].extend(matches)
    
    # Extract subsections (उपदफा)
    subsection_patterns = [
        r"\((\d+)\)",
        r"उपदफा\s*\((\d+)\)"
    ]
    for pattern in subsection_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references["subsections"].extend(matches)
    
    # Remove duplicates
    for key in references:
        references[key] = list(set(references[key]))
    
    return references

logger = setup_logging()
