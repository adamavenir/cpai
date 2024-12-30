"""Module for validating content size."""
import tiktoken
from typing import Dict, Any
from colorama import Fore, Style, init
from .constants import (
    CHATGPT_CHAR_LIMIT,
    CLAUDE_CHAR_LIMIT,
    O1_API_TOKEN_LIMIT,
    SONNET_API_TOKEN_LIMIT,
    FOURTHBRAIN_API_TOKEN_LIMIT,
    TOKEN_BUFFER,
    COMPAT_CHECK,
    COMPAT_X
)

# Initialize colorama
init()

def format_number(num: int) -> str:
    """Format a number with commas."""
    return f"{num:,}"

def check_model_compatibility(chars: int, tokens: int) -> str:
    """Check content compatibility with different models."""
    models = [
        ("ChatGPT", chars <= CHATGPT_CHAR_LIMIT),
        ("Claude", chars <= CLAUDE_CHAR_LIMIT),
        ("o1 API", tokens <= O1_API_TOKEN_LIMIT - TOKEN_BUFFER),
        ("Sonnet API", tokens <= SONNET_API_TOKEN_LIMIT - TOKEN_BUFFER),
        ("4o API", tokens <= FOURTHBRAIN_API_TOKEN_LIMIT - TOKEN_BUFFER)
    ]
    
    result = "Output content compatibility:\n"
    for name, compatible in models:
        symbol = COMPAT_CHECK if compatible else COMPAT_X
        color = Fore.GREEN if compatible else Fore.RED
        result += f"{color}{symbol}{Style.RESET_ALL} {name}  "
    
    return result

def validate_content_size(content: str, max_size: int = None) -> Dict[str, Any]:
    """Validate content size and return size information."""
    # Get character count
    char_count = len(content)
    
    # Get token count using tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    token_count = len(enc.encode(content))
    
    # Format numbers for display
    formatted_chars = format_number(char_count)
    formatted_tokens = format_number(token_count)
    
    # Check model compatibility
    compatibility = check_model_compatibility(char_count, token_count)
    
    return {
        'chars': char_count,
        'tokens': token_count,
        'formatted_chars': formatted_chars,
        'formatted_tokens': formatted_tokens,
        'compatibility': compatibility,
        'exceeds_limit': max_size and char_count > max_size,
        'formatted_max_size': format_number(max_size) if max_size else None
    } 