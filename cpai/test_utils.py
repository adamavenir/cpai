"""Utilities for handling test execution and code extraction."""

import os
import ast
import logging
from typing import List, Dict, Optional, Tuple
from .source_analysis import analyze_test_file, extract_source_code

def extract_test_function(file_path: str, function_name: str) -> Optional[str]:
    """Extract a specific test function from a file.
    
    Args:
        file_path: Path to the test file
        function_name: Name of the test function to extract
        
    Returns:
        String containing the test function code, or None if not found
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Get the lines for this function
                start_line = node.lineno
                end_line = node.end_lineno
                
                # Get the actual source lines
                lines = content.splitlines()
                return '\n'.join(lines[start_line - 1:end_line])
                
        return None
    except Exception as e:
        logging.error(f"Failed to extract test function: {e}")
        return None

def parse_nodeid(nodeid: str) -> Tuple[str, str]:
    """Parse a pytest nodeid into file path and test name.
    
    Args:
        nodeid: pytest nodeid (e.g. 'tests/test_main.py::test_function')
        
    Returns:
        Tuple of (file_path, function_name)
    """
    parts = nodeid.split("::")
    return parts[0], parts[-1]

def extract_failing_tests(test_results: Dict, include_source: bool = False) -> List[Dict[str, str]]:
    """Extract code from failing tests.
    
    Args:
        test_results: Dictionary containing test results from pytest
        include_source: Whether to include related source code
        
    Returns:
        List of dictionaries containing test info and code
    """
    failing_tests = []
    logging.debug(f"Processing test results with include_source={include_source}")
    
    for test in test_results.get('tests', []):
        if test.get('outcome') == 'failed':
            file_path, func_name = parse_nodeid(test['nodeid'])
            logging.debug(f"Processing failing test: {file_path}::{func_name}")
            code = extract_test_function(file_path, func_name)
            
            if code:
                test_info = {
                    'file': file_path,
                    'function': func_name,
                    'code': code,
                    'message': test.get('call', {}).get('longrepr', '')
                }
                
                # Add source code if requested
                if include_source:
                    logging.debug("Including source code for failing test")
                    # Get source files from test file
                    source_files = analyze_test_file(file_path, test_mode=True)
                    logging.debug(f"Found source files: {source_files}")
                    if source_files:
                        source_code = extract_source_code(source_files)
                        if source_code:
                            test_info['source_code'] = source_code
                            logging.debug(f"Added source code for modules: {list(source_code.keys())}")
                            
                    # Also get source files from any imports in the test function
                    try:
                        tree = ast.parse(code)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.Import, ast.ImportFrom)):
                                if isinstance(node, ast.Import):
                                    for name in node.names:
                                        if name.name.startswith('cpai.'):
                                            module_name = name.name
                                            logging.debug(f"Found import: {module_name}")
                                            if source_file := find_source_file(module_name, get_search_paths(file_path)):
                                                source_files[module_name] = source_file
                                                logging.debug(f"Added source file: {source_file}")
                                elif node.module and node.module.startswith('cpai.'):
                                    module_name = node.module
                                    logging.debug(f"Found from import: {module_name}")
                                    if source_file := find_source_file(module_name, get_search_paths(file_path)):
                                        source_files[module_name] = source_file
                                        logging.debug(f"Added source file: {source_file}")
                                        
                        # Extract code from additional source files
                        additional_code = extract_source_code(source_files)
                        if additional_code:
                            if 'source_code' not in test_info:
                                test_info['source_code'] = {}
                            test_info['source_code'].update(additional_code)
                            logging.debug(f"Added additional source code for modules: {list(additional_code.keys())}")
                    except Exception as e:
                        logging.error(f"Failed to analyze test function imports: {e}")
                
                failing_tests.append(test_info)
            
    return failing_tests

def format_test_output(failing_tests: List[Dict[str, str]]) -> str:
    """Format failing tests into markdown output.
    
    Args:
        failing_tests: List of failing test info from extract_failing_tests
        
    Returns:
        Markdown formatted string
    """
    if not failing_tests:
        return "No failing tests found."
        
    output = ["## Failing Tests\n"]
    
    for test in failing_tests:
        output.append(f"### {test['file']}::{test['function']}\n")
        output.append("```python")
        output.append(test['code'])
        output.append("```\n")
        if test['message']:
            output.append("#### Error Message")
            output.append("```")
            output.append(test['message'])
            output.append("```\n")
            
        # Add source code if available
        if source_code := test.get('source_code'):
            output.append("#### Related Source Code\n")
            for module_name, code in source_code.items():
                output.append(f"##### {module_name}")
                output.append("```python")
                output.append(code)
                output.append("```\n")
            
    return '\n'.join(output) 