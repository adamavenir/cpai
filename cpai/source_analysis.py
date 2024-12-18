"""Utilities for analyzing source code dependencies."""

import ast
import os
import logging
from typing import List, Set, Dict, Optional
import re
from pathlib import Path

def extract_imports(file_path: str) -> Set[str]:
    """Extract all imports from a JavaScript/TypeScript file.
    
    Args:
        file_path: Path to the JavaScript/TypeScript file
        
    Returns:
        Set of import paths found in the file
    """
    imports = set()
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Remove indentation
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        content = '\n'.join(lines)
        
        # Match ES6 imports
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',  # import x from 'y'
            r'import\s+[\'"]([^\'"]+)[\'"]',  # import 'y'
            r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # import('y')
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # require('y')
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                imports.add(match.group(1))
        
        return imports
    except Exception as e:
        print(f"Error extracting imports from {file_path}: {e}")
        return set()

def find_source_file(import_path: str, search_paths: List[str]) -> Optional[str]:
    """Find the actual source file for a given import path.
    
    Args:
        import_path: The import path from the import statement
        search_paths: List of directories to search in
        
    Returns:
        Full path to the source file if found, None otherwise
    """
    # Handle relative imports
    if import_path.startswith('.'):
        # Count the number of parent directories to traverse
        parent_count = import_path.count('../')
        if parent_count > 0:
            import_path = import_path[(parent_count * 3):]  # Remove '../' prefixes
        else:
            import_path = import_path[2:]  # Remove './' prefix
    
    # List of possible extensions
    extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']
    
    for search_path in search_paths:
        # Try with and without 'src' directory
        paths_to_try = [
            Path(search_path) / import_path,
            Path(search_path) / 'src' / import_path
        ]
        
        for base_path in paths_to_try:
            # Try exact path first
            if base_path.exists():
                if base_path.is_dir():
                    # Try index files in directory
                    for ext in extensions:
                        index_file = base_path / f'index{ext}'
                        if index_file.exists():
                            return str(index_file)
                else:
                    return str(base_path)
            
            # Try with extensions
            for ext in extensions:
                file_path = base_path.with_suffix(ext)
                if file_path.exists():
                    return str(file_path)
    
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
    """Analyze a test file and find all related source files.
    
    Args:
        test_file: Path to the test file
        test_mode: Whether to include test-related imports
        
    Returns:
        Dictionary mapping import paths to source file paths
    """
    source_files = {}
    test_dir = os.path.dirname(test_file)
    
    # Get base source directory (assuming standard project structure)
    src_dir = test_dir
    if 'tests' in test_dir or '__tests__' in test_dir:
        src_dir = re.sub(r'/?tests/?|/__tests__/?', '', test_dir)
    
    # Add parent directories for relative imports
    search_paths = [
        test_dir,  # For imports relative to test file
        src_dir,   # For source files
        os.path.dirname(src_dir),  # For parent directory imports
    ]
    
    # Extract and resolve imports
    imports = extract_imports(test_file)
    for import_path in imports:
        # Skip node_modules and test utilities unless in test mode
        if (not test_mode and 
            (import_path.startswith('@') or 
             'node_modules' in import_path or 
             'test-utils' in import_path)):
            continue
        
        # Handle relative imports
        if import_path.startswith('.'):
            # Get absolute path relative to test file
            abs_path = os.path.normpath(os.path.join(test_dir, import_path))
            source_file = find_source_file(abs_path, [os.path.dirname(abs_path)])
        else:
            source_file = find_source_file(import_path, search_paths)
        
        if source_file:
            source_files[import_path] = source_file
            
            # Recursively analyze imported source files
            if source_file != test_file:  # Avoid circular imports
                nested_sources = analyze_test_file(source_file, test_mode=False)
                source_files.update(nested_sources)
    
    # Add test file itself
    source_files['test_file'] = test_file
    
    return source_files

def extract_source_code(source_files: Dict[str, str]) -> Dict[str, str]:
    """Extract source code from all related files.
    
    Args:
        source_files: Dictionary mapping import paths to source file paths
        
    Returns:
        Dictionary mapping file paths to their source code
    """
    source_code = {}
    
    # Get unique file paths (including test file)
    file_paths = set(source_files.values())
    if 'test_file' in source_files:
        file_paths.add(source_files['test_file'])
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Remove indentation
            lines = content.split('\n')
            lines = [line.strip() for line in lines]
            content = '\n'.join(lines)
            
            source_code[file_path] = content
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return source_code 