"""Module for analyzing test files and extracting source code."""

import os
import ast
import re
import logging
from typing import List, Set, Dict, Optional

def is_stdlib_module(module_name: str) -> bool:
    """Check if a module is from the standard library.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if the module is from the standard library
    """
    import sys
    import pkgutil
    
    stdlib_modules = {module.name for module in pkgutil.iter_modules()}
    stdlib_modules.update(sys.stdlib_module_names)
    
    # Get the base module name (before any dots)
    base_module = module_name.split('.')[0]
    return base_module in stdlib_modules

def get_search_paths(file_path: str) -> List[str]:
    """Get search paths for finding source files.
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of directory paths to search
    """
    # Get the directory containing the file
    file_dir = os.path.dirname(file_path)
    logging.debug(f"Getting search paths for test file: {file_path}")
    
    # Add parent directories up to the project root
    search_paths = []
    current_dir = file_dir
    while current_dir and os.path.basename(current_dir):
        search_paths.append(current_dir)
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    
    logging.debug(f"Search paths: {search_paths}")
    return search_paths

def get_imports(file_path: str) -> Set[str]:
    """Get all imports from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Set of imported module names
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        imports = set()
        
        # Parse Python code
        tree = ast.parse(content)
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    
        return imports
        
    except Exception as e:
        logging.error(f"Failed to get imports from {file_path}: {e}")
        return set()

def find_source_file(module_name: str, search_paths: List[str]) -> Optional[str]:
    """Find a source file for a module.
    
    Args:
        module_name: Name of the module to find
        search_paths: List of directories to search
        
    Returns:
        Path to the source file, or None if not found
    """
    # Convert module name to path
    module_path = module_name.replace('.', os.sep)
    
    # Try different file extensions
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx']
    
    for search_path in search_paths:
        for ext in extensions:
            file_path = os.path.join(search_path, module_path + ext)
            if os.path.exists(file_path):
                return file_path
                
            # Try as directory with __init__.py
            init_path = os.path.join(search_path, module_path, '__init__.py')
            if os.path.exists(init_path):
                return init_path
                
    return None

def analyze_test_file(test_file: str, test_mode: bool = True, visited: Optional[Set[str]] = None) -> List[str]:
    """Analyze a test file to find related source files.
    
    Args:
        test_file: Path to the test file
        test_mode: Whether to analyze test files or source files
        visited: Set of already visited files to prevent recursion
        
    Returns:
        List of source file paths
    """
    if visited is None:
        visited = set()
        
    if test_file in visited:
        return []
        
    visited.add(test_file)
    
    try:
        # Get search paths for this file
        search_paths = get_search_paths(test_file)
        logging.debug(f"Search paths: {search_paths}")
        
        # Get imports from the file
        imports = get_imports(test_file)
        
        # Find source files
        source_files = []
        for imp in imports:
            # Skip standard library imports
            if is_stdlib_module(imp):
                continue
                
            # Try to find the source file
            source_file = find_source_file(imp, search_paths)
            if source_file:
                source_files.append(source_file)
                
                # Recursively analyze imported source files
                if test_mode:
                    nested_sources = analyze_test_file(source_file, test_mode=False, visited=visited)
                    source_files.extend(nested_sources)
        
        return list(set(source_files))  # Remove duplicates
        
    except Exception as e:
        logging.error(f"Failed to analyze test file {test_file}: {e}")
        return []

def extract_source_code(source_files: List[str]) -> Dict[str, str]:
    """Extract code from source files.
    
    Args:
        source_files: List of source file paths
        
    Returns:
        Dictionary mapping file paths to their content
    """
    source_code = {}
    
    for file_path in source_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                source_code[file_path] = content
        except Exception as e:
            logging.error(f"Failed to read source file {file_path}: {e}")
            
    return source_code 