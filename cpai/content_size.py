"""Module for handling content size validation and character counting."""
import logging
from typing import List, Dict, Any, Optional
import tiktoken
from .constants import DEFAULT_CHUNK_SIZE

def tokenize(text: str) -> List[int]:
    """Tokenize text using tiktoken or fallback to simple tokenization."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode(text)
    except Exception as e:
        logging.debug(f"Failed to use tiktoken: {e}")
        # Simple fallback tokenization
        return text.split()

def get_content_size(content: str) -> Dict[str, int]:
    """Get the size of content in characters and tokens.
    
    Args:
        content: The content to measure
        
    Returns:
        Dictionary with 'chars' and 'tokens' counts
    """
    char_count = len(content)
    token_count = len(tokenize(content))
    return {
        'chars': char_count,
        'tokens': token_count
    }

def format_size_info(size_info: Dict[str, int]) -> Dict[str, str]:
    """Format size information with commas.
    
    Args:
        size_info: Dictionary with 'chars' and 'tokens' counts
        
    Returns:
        Dictionary with formatted strings
    """
    return {
        'chars': f"{size_info['chars']:,}",
        'tokens': f"{size_info['tokens']:,}"
    }

def validate_content_size(content: str, max_size: Optional[int] = None) -> Dict[str, Any]:
    """Validate content size against maximum limit.
    
    Args:
        content: The content to validate
        max_size: Maximum allowed size in characters (default: DEFAULT_CHUNK_SIZE)
        
    Returns:
        Dictionary with size information and validation result
    """
    if max_size is None:
        max_size = DEFAULT_CHUNK_SIZE
        
    # Get size information
    size_info = get_content_size(content)
    formatted = format_size_info(size_info)
    
    # Check if content exceeds maximum size
    exceeds_limit = size_info['chars'] > max_size
    
    return {
        'chars': size_info['chars'],
        'tokens': size_info['tokens'],
        'formatted_chars': formatted['chars'],
        'formatted_tokens': formatted['tokens'],
        'exceeds_limit': exceeds_limit,
        'max_size': max_size,
        'formatted_max_size': f"{max_size:,}"
    } 