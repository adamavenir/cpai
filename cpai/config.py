"""Module for handling configuration and logging setup."""
import json
import logging
from typing import Dict, Any
from .constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_FILE_EXTENSIONS
)

def configure_logging(debug: bool) -> None:
    """Configure logging based on debug flag.
    
    Args:
        debug: Whether to enable debug logging
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

def read_config() -> Dict[str, Any]:
    """Read and validate configuration from file.
    
    Returns:
        Configuration dictionary with defaults applied
    """
    logging.debug("Reading configuration")
    default_config = {
        "include": ["**/*"],
        "exclude": DEFAULT_EXCLUDE_PATTERNS.copy(),
        "outputFile": False,
        "usePastebin": True,
        "fileExtensions": DEFAULT_FILE_EXTENSIONS,
        "chunkSize": DEFAULT_CHUNK_SIZE
    }
    
    try:
        with open('cpai.config.json', 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                logging.warning("Invalid JSON in config file. Using default configuration.")
                return default_config
                
            # Handle exclude patterns
            if 'exclude' in config:
                if config['exclude'] is None:
                    # Keep default exclude patterns if user config has null
                    config.pop('exclude')
                elif not isinstance(config['exclude'], list):
                    logging.warning("Invalid 'exclude' in config. Using default.")
                    config.pop('exclude')
                else:
                    # Start with default patterns and add user patterns
                    default_config['exclude'].extend([str(pattern) for pattern in config['exclude']])
                    config['exclude'] = default_config['exclude']
                    
            # Validate other fields and update config
            if isinstance(config.get('outputFile'), (bool, str)):
                default_config.update(config)
            else:
                logging.warning("Invalid 'outputFile' in config. Using default.")
                
            # Ensure chunkSize is an integer
            if 'chunkSize' in config:
                if isinstance(config['chunkSize'], int):
                    default_config['chunkSize'] = config['chunkSize']
                else:
                    logging.warning("Invalid 'chunkSize' in config. Using default.")
                    
            return default_config
            
    except FileNotFoundError:
        logging.debug("Configuration file not found. Using default configuration.")
        return default_config 