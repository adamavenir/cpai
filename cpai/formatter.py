"""Module for handling tree-building, path-based formatting, and function-outline rendering."""
import os
import logging
from typing import List, Dict, Any, Optional
from .outline.base import FunctionInfo, OutlineExtractor
from .outline import EXTRACTORS
from .file_selection import get_relative_path

def get_extractor_for_ext(ext: str) -> Optional[OutlineExtractor]:
    """Get the appropriate extractor for a file extension."""
    # Create a dummy filename with the extension
    dummy_file = f"test{ext}"
    for extractor in EXTRACTORS:
        if extractor.supports_file(dummy_file):
            return extractor
    return None

def get_language_from_ext(ext: str) -> str:
    """Get language name from file extension."""
    ext = ext.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'cpp',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.m': 'objectivec',
        '.mm': 'objectivec',
        '.pl': 'perl',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.fish': 'fish',
        '.sql': 'sql',
        '.r': 'r',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.md': 'markdown',
        '.css': 'css',
        '.scss': 'scss',
        '.less': 'less',
        '.html': 'html',
        '.vue': 'vue',
        '.sol': 'solidity'
    }
    return language_map.get(ext, '')

def format_functions_as_tree(functions: List[FunctionInfo], indent: str = '', extractor: Optional[OutlineExtractor] = None) -> str:
    """Format a list of functions as a tree structure."""
    if not functions:
        return ''
        
    # Group functions by class/namespace
    grouped = {}
    standalone = []
    
    for func in functions:
        if '.' in func.name:
            # This is a class method or namespaced function
            parent, name = func.name.rsplit('.', 1)
            if parent not in grouped:
                grouped[parent] = []
            # Create a new FunctionInfo instance with the short name
            grouped[parent].append(FunctionInfo(
                name=name,
                line_number=func.line_number,
                parameters=func.parameters,
                leading_comment=func.leading_comment,
                is_export=func.is_export,
                is_default_export=func.is_default_export,
                node_type=func.node_type
            ))
        else:
            standalone.append(func)
            
    # Format the tree
    result = []
    
    # Add standalone functions first
    for func in standalone:
        if func.node_type == 'class':
            # Skip classes as they'll be handled with their methods
            continue
        result.append(f"{indent}├── {func.name}")
        
    # Add classes and their methods
    for class_name, methods in grouped.items():
        # Add the class
        result.append(f"{indent}├── {class_name}")
        
        # Add its methods
        for method in methods:
            # Use different prefix for last item
            prefix = '└──' if method == methods[-1] else '├──'
            result.append(f"{indent}│   {prefix} {method.name}")
            
    return '\n'.join(result)

def format_outline_tree(files: Dict[str, Dict], options: Dict) -> Dict[str, str]:
    """Format file outlines as a tree structure."""
    result = {}
    
    for file_path, file_data in files.items():
        outline = file_data.get('outline', [])
        if outline:
            # Get the appropriate extractor for this file type
            ext = os.path.splitext(file_path)[1]
            extractor = get_extractor_for_ext(ext)
            
            # Format the functions as a tree
            tree = format_functions_as_tree(outline, extractor=extractor)
            if tree:  # Only include files that have functions
                result[file_path] = tree
                
    return result

def build_tree_structure(files_dict: Dict[str, str]) -> Dict:
    """Build a tree structure from a dictionary of file paths."""
    tree = {}
    
    for file_path, content in files_dict.items():
        current = tree
        parts = file_path.split(os.sep)
        
        # Process all but the last part (the file name)
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Add the file and its content
        current[parts[-1]] = content
        
    return tree

def format_tree_with_outlines(tree: Dict, indent: str = '') -> str:
    """Format a tree structure with function outlines."""
    result = []
    
    for name, content in tree.items():
        if isinstance(content, dict):
            # This is a directory
            result.append(f"{indent}├── {name}/")
            result.append(format_tree_with_outlines(content, indent + "│   "))
        else:
            # This is a file
            result.append(f"{indent}├── {name}")
            if content:  # If there are functions
                # Add the function tree with additional indentation
                result.append(content.replace('\n', f'\n{indent}│   '))
                
    return '\n'.join(result)

def format_content(files: Dict[str, Dict], options: Dict) -> str:
    """Format the content of files."""
    if options.get('tree'):
        # Get outlines in tree format
        outlines = format_outline_tree(files, options)
        
        # Build and format the tree
        tree = build_tree_structure(outlines)
        return format_tree_with_outlines(tree)
    
    # Regular format (full content)
    result = []
    for file_path, file_data in files.items():
        if file_data is None:  # Skip failed files
            continue
            
        # Add file header
        result.append(f"# {file_path}")
        result.append("")
        
        # Add outline if available
        outline = file_data.get('outline', [])
        if outline:
            result.append("## Functions")
            for func in outline:
                result.append(f"- {func.name}")
            result.append("")
            
        # Add file content
        content = file_data.get('content', '')
        if content:
            result.append("## Content")
            result.append("```" + get_language_from_ext(os.path.splitext(file_path)[1]))
            result.append(content)
            result.append("```")
            
    return '\n'.join(result)

def format_tree(files: List[str]) -> str:
    """Format a list of files as a tree structure."""
    # Convert list of files to dictionary structure
    tree = {}
    for file_path in files:
        current = tree
        parts = file_path.split(os.sep)
        
        # Process all but the last part (the file name)
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Add the file
        current[parts[-1]] = None  # No content for files in tree view
        
    return format_tree_string(tree)

def format_tree_string(tree: Dict, prefix: str = '', is_last: bool = True) -> str:
    """Format a tree dictionary as a string."""
    result = []
    items = list(tree.items())
    
    for i, (name, subtree) in enumerate(items):
        is_last_item = i == len(items) - 1
        
        # Add current item
        result.append(f"{prefix}{'└──' if is_last_item else '├──'} {name}")
        
        # Add subtree if it exists
        if isinstance(subtree, dict):
            extension = '    ' if is_last_item else '│   '
            subtree_str = format_tree_string(subtree, prefix + extension, is_last_item)
            if subtree_str:
                result.append(subtree_str)
                
    return '\n'.join(result)

def generate_tree(files: List[str]) -> str:
    """Generate a tree view of files."""
    if not files:
        return "```\nNo files found.\n```\n"
        
    # Sort files to ensure consistent order
    files = sorted(files)
    
    # Generate directory structure
    tree_lines = ['```']
    base_dir = os.path.commonpath([os.path.abspath(f) for f in files]) if files else ''
    
    for file in files:
        # Ensure the path is relative and uses forward slashes
        rel_path = get_relative_path(file)
        tree_lines.append(f"    {rel_path}")
    tree_lines.append('```\n')
    
    # Generate function tree for each file
    for file in files:
        abs_path = os.path.abspath(file)
        ext = os.path.splitext(file)[1]
        extractor = get_extractor_for_ext(ext)
        
        if extractor and os.path.exists(abs_path):
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                functions = extractor.extract_functions(content)
                
                if functions:
                    tree_lines.append(f'\n## {get_relative_path(file)}')
                    current_class = None
                    
                    for func in functions:
                        indent = '    ' if '.' in func.name else ''
                        tree_lines.append(f'{indent}└── {func.name}')
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
    
    return '\n'.join(tree_lines) 