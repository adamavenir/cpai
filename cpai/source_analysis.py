"""Utilities for analyzing source code dependencies."""

import ast
import os
import logging
from typing import List, Set, Dict, Optional

def extract_imports(file_path: str) -> List[str]:
    """Extract all imports from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of imported module names
    """
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Handles 'from x import y'
                    imports.add(node.module)
                
        return sorted(list(imports))
    except Exception as e:
        logging.error(f"Failed to extract imports from {file_path}: {e}")
        return []

def find_source_file(module_name: str, search_paths: List[str]) -> Optional[str]:
    """Find the source file for a given module name.
    
    Args:
        module_name: Name of the module to find
        search_paths: List of paths to search in
        
    Returns:
        Path to the source file if found, None otherwise
    """
    # Convert module path to file path
    module_parts = module_name.split('.')
    module_path = os.path.join(*module_parts)
    
    possible_files = [
        f"{module_path}.py",  # Single file module
        os.path.join(module_path, "__init__.py"),  # Package module
        os.path.join('cpai', module_path.replace('cpai.', '') + '.py'),  # Try in cpai directory
        os.path.join('cpai', module_path.replace('cpai.', ''), "__init__.py")  # Try in cpai package
    ]
    
    logging.debug(f"Searching for module {module_name} in paths: {search_paths}")
    logging.debug(f"Possible files: {possible_files}")
    
    for path in search_paths:
        for file in possible_files:
            full_path = os.path.join(path, file)
            if os.path.exists(full_path):
                logging.debug(f"Found source file: {full_path}")
                return full_path
    
    logging.debug(f"Source file not found for module: {module_name}")
    return None

def get_search_paths(test_file: str) -> List[str]:
    """Get list of paths to search for source files.
    
    Args:
        test_file: Path to the test file
        
    Returns:
        List of paths to search in
    """
    # Convert test file to absolute path
    test_file = os.path.abspath(test_file)
    logging.debug(f"Getting search paths for test file: {test_file}")
    
    # Start with the test file's directory
    test_dir = os.path.dirname(test_file)
    paths = [test_dir]
    
    # Add parent directory
    parent = os.path.dirname(test_dir)
    paths.append(parent)
    
    # Add common source directories relative to parent
    common_dirs = ['src', 'lib', 'app', 'source', 'cpai']
    paths.extend([os.path.join(parent, d) for d in common_dirs])
    
    # Add Python path
    paths.extend(os.environ.get('PYTHONPATH', '').split(os.pathsep))
    
    # Filter out empty or nonexistent paths
    paths = [p for p in paths if p and os.path.exists(p)]
    
    # Add the parent directory again to handle package imports
    if parent not in paths:
        paths.append(parent)
    
    logging.debug(f"Search paths: {paths}")
    return paths

def analyze_test_file(test_file: str, test_mode: bool = False) -> Dict[str, str]:
    """Analyze a test file and find its source dependencies.
    
    Args:
        test_file: Path to the test file
        test_mode: If True, process all imports, not just cpai.* imports
        
    Returns:
        Dictionary mapping module names to source file paths
    """
    # Get imports from test file
    imports = extract_imports(test_file)
    if not imports:
        return {}
        
    # Get search paths
    search_paths = get_search_paths(test_file)
    
    # Find source files for each import and their dependencies
    source_files = {}
    processed = set()
    
    def process_module(module_name: str):
        if module_name in processed:
            return
        processed.add(module_name)
        
        if source_file := find_source_file(module_name, search_paths):
            source_files[module_name] = source_file
            # Process imports from this module
            module_imports = extract_imports(source_file)
            for imp in module_imports:
                if test_mode or imp.startswith('cpai.'):  # Process all imports in test mode
                    process_module(imp)
    
    # Process all imports recursively
    for module_name in imports:
        if test_mode or module_name.startswith('cpai.'):  # Process all imports in test mode
            process_module(module_name)
            
    return source_files

def extract_source_code(source_files: Dict[str, str]) -> Dict[str, str]:
    """Extract code from source files.
    
    Args:
        source_files: Dictionary mapping module names to file paths
        
    Returns:
        Dictionary mapping module names to their source code
    """
    source_code = {}
    for module_name, file_path in source_files.items():
        try:
            with open(file_path, 'r') as f:
                source_code[module_name] = f.read()
        except Exception as e:
            logging.error(f"Failed to read source file {file_path}: {e}")
            
    return source_code 