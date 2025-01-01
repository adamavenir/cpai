"""Module for handling file selection and filtering logic."""
import os
import logging
import fnmatch
from typing import List, Dict
import pathspec
from .constants import (
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_FILE_EXTENSIONS
)

def get_relative_path(path: str) -> str:
    """Get relative path from current directory."""
    rel_path = os.path.relpath(path)
    # Remove ./ prefix if present
    if rel_path.startswith('./'):
        rel_path = rel_path[2:]
    return rel_path

def should_match_pattern(path: str, pattern: str) -> bool:
    """Check if a path matches a pattern, handling directory patterns correctly."""
    # Normalize paths to use forward slashes
    path = path.replace(os.sep, '/')
    pattern = pattern.replace(os.sep, '/')
    
    # Handle directory patterns
    if pattern.endswith('/'):
        # Check if path starts with the pattern or is a subdirectory
        pattern = pattern.rstrip('/')
        path_parts = path.split('/')
        return pattern in path_parts
        
    # Handle file patterns (including globs)
    return fnmatch.fnmatch(path, pattern)

def get_files(directory: str, config: Dict = None, include_all: bool = False) -> List[str]:
    """Get list of files to process.
    
    Args:
        directory: Directory to search
        config: Configuration dictionary
        include_all: Whether to include all file types
        
    Returns:
        List of relative file paths to process
    """
    if config is None:
        config = {}

    # Ensure we have absolute path for directory
    directory = os.path.abspath(directory)
    logging.debug(f"Searching directory: {directory}")
    
    # Get patterns from config
    include_patterns = config.get('include', ['**/*'])  # Default to all files
    custom_excludes = config.get('exclude', [])
    file_extensions = [] if include_all else config.get('fileExtensions', [])
    
    # If nodocs is set, exclude .md files
    if config.get('nodocs'):
        custom_excludes.append('**/*.md')
    
    # Adjust patterns if we're searching in a subdirectory
    base_dir = os.path.basename(directory)
    adjusted_patterns = []
    for pattern in include_patterns:
        if pattern.startswith(f"{base_dir}/"):
            # Remove the base directory prefix since we're already in that directory
            pattern = pattern[len(base_dir)+1:]
            logging.debug(f"Adjusted pattern from {include_patterns} to {pattern}")
        adjusted_patterns.append(pattern)
    include_patterns = adjusted_patterns
    
    logging.debug(f"Include patterns: {include_patterns}")
    logging.debug(f"Exclude patterns: {custom_excludes}")
    logging.debug(f"File extensions: {file_extensions}")
    logging.debug(f"include_all: {include_all}")
    logging.debug(f"config.include_all: {config.get('include_all', False)}")
    
    # Start with default exclude patterns only if not include_all
    exclude_patterns = []
    if not include_all and not config.get('include_all', False):
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.copy()
        logging.debug(f"Using default exclude patterns: {exclude_patterns}")
        
    if custom_excludes:
        if isinstance(custom_excludes, list):
            exclude_patterns.extend(custom_excludes)
    
    # Add .gitignore patterns if .gitignore exists and not include_all
    gitignore_path = os.path.join(directory, '.gitignore')
    if os.path.exists(gitignore_path) and not config.get('include_all', False):
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_patterns = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('!'):
                        # Handle negation patterns
                        pattern = line[1:]  # Remove !
                        if pattern.startswith('/'):
                            pattern = pattern[1:]  # Remove leading slash
                        gitignore_patterns.append(f"!{pattern}")  # Keep the ! prefix
                    else:
                        if line.startswith('/'):
                            line = line[1:]  # Remove leading slash
                        gitignore_patterns.append(line)
                exclude_patterns.extend(gitignore_patterns)
        except Exception as e:
            logging.warning(f"Failed to read .gitignore: {e}")
    
    logging.debug(f"Final exclude patterns: {exclude_patterns}")
    
    # Create gitignore spec for exclude patterns
    exclude_spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern,
        exclude_patterns if exclude_patterns else ['']  # Avoid empty list error
    )
    
    # Get all files recursively
    all_files = []
    for root, _, files in os.walk(directory, followlinks=True):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip broken symlinks
            if os.path.islink(file_path):
                real_path = os.path.realpath(file_path)
                exists = os.path.exists(real_path)
                logging.debug(f"Found symlink {file_path} -> {real_path} (exists: {exists})")
                if not exists:
                    logging.debug(f"Skipping broken symlink: {file_path}")
                    continue
                
            # Get relative path from the search directory
            rel_path = os.path.relpath(file_path, directory)
            logging.debug(f"\nProcessing file: {rel_path}")
            
            # Skip if matches exclude patterns
            if exclude_patterns and exclude_spec.match_file(rel_path):
                # Check for negation patterns
                negated = False
                for pattern in exclude_patterns:
                    if pattern.startswith('!'):
                        pattern = pattern[1:]  # Remove !
                        if pathspec.patterns.GitWildMatchPattern(pattern).match_file(rel_path):
                            negated = True
                            logging.debug(f"File {rel_path} negated by pattern !{pattern}")
                            break
                if not negated:
                    logging.debug(f"Excluding {rel_path} due to exclude pattern")
                    continue
                
            # Skip if doesn't match include patterns
            matched = False
            for pattern in include_patterns:
                # Convert pattern to use forward slashes
                pattern = pattern.replace(os.sep, '/')
                logging.debug(f"Checking include pattern: {pattern}")
                
                # Create a pathspec for this pattern
                spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern,
                    [pattern]
                )
                
                # Convert path to use forward slashes for matching
                check_path = rel_path.replace(os.sep, '/')
                logging.debug(f"Checking path {check_path} against pattern {pattern}")
                
                if spec.match_file(check_path):
                    matched = True
                    logging.debug(f"File {check_path} matches pattern {pattern}")
                    break
                else:
                    logging.debug(f"File {check_path} does not match pattern {pattern}")
                    
            if not matched:
                logging.debug(f"Excluding {rel_path} due to not matching include pattern")
                continue
                
            # Check file extension if not including all files
            if file_extensions:
                ext = os.path.splitext(file)[1].lower()
                if not ext or ext not in file_extensions:
                    logging.debug(f"Excluding {rel_path} due to file extension {ext}")
                    continue
            
            logging.debug(f"Including file: {rel_path}")
            all_files.append(rel_path)  # Store relative path
    
    return sorted(all_files)

def should_process_file(file_path: str, config: Dict) -> bool:
    """Determine if a file should be processed based on configuration.
    
    Args:
        file_path: Path to the file
        config: Configuration dictionary
        
    Returns:
        True if file should be processed, False otherwise
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Check if docs should be excluded
    if config.get('nodocs') and ext == '.md':
        logging.debug(f"File {file_path} excluded due to nodocs flag")
        return False
    
    # Check if extension is in allowed list
    if 'fileExtensions' in config and ext not in config['fileExtensions']:
        logging.debug(f"File {file_path} excluded due to extension {ext} not in {config['fileExtensions']}")
        return False
        
    # Get relative path for pattern matching
    rel_path = get_relative_path(file_path)
    logging.debug(f"Checking file {rel_path} against patterns")
    
    # Check exclude patterns
    exclude_patterns = config.get('exclude', [])
    for pattern in exclude_patterns:
        if pattern.startswith('!'):
            # Handle negation patterns
            pattern = pattern[1:]  # Remove !
            if should_match_pattern(rel_path, pattern):
                logging.debug(f"File {rel_path} included by negation pattern !{pattern}")
                return True
        elif should_match_pattern(rel_path, pattern):
            logging.debug(f"File {rel_path} excluded by pattern {pattern}")
            return False
            
    # Check include patterns
    include_patterns = config.get('include', ['**/*'])
    logging.debug(f"Checking include patterns: {include_patterns}")
    
    # Try to match against each include pattern
    for pattern in include_patterns:
        # Convert pattern to use forward slashes
        pattern = pattern.replace(os.sep, '/')
        
        # If pattern doesn't start with **, make it match anywhere in the path
        if not pattern.startswith('**'):
            pattern = f"**/{pattern}"
        
        # Create a pathspec for this pattern
        spec = pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern,
            [pattern]
        )
        
        # Convert path to use forward slashes for matching
        check_path = rel_path.replace(os.sep, '/')
        
        if spec.match_file(check_path):
            logging.debug(f"File {rel_path} matches include pattern {pattern}")
            return True
            
    logging.debug(f"File {rel_path} does not match any include patterns")
    return False 