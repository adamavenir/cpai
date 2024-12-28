"""Utilities for handling test execution and code extraction."""

import os
import ast
import json
import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from .source_analysis import analyze_test_file, extract_source_code

def run_test_command(command: str) -> Optional[Dict]:
    """Run a test command and return the test results.
    
    Args:
        command: The test command to run (e.g. 'pytest', 'jest', 'vitest')
        
    Returns:
        Dict containing the test results, or None if execution failed
    """
    try:
        # Add appropriate flags based on test runner
        if command.startswith('pytest'):
            if '--json-report' not in command:
                command = f"{command} --json-report"
            if '--json-report-file' not in command:
                command = f"{command} --json-report-file=.report.json"
            logging.debug(f"Running pytest command: {command}")
            
        elif command.startswith('jest'):
            if '--json' not in command:
                command = f"{command} --json"
        elif command.startswith('vitest'):
            if '--reporter=json' not in command:
                command = f"{command} --reporter=json"
            
        # Run the command
        result = subprocess.run(command.split(), capture_output=True, text=True)
        logging.debug(f"Command stderr: {result.stderr}")
        
        # Parse results based on test runner
        if command.startswith('pytest'):
            try:
                with open('.report.json', 'r') as f:
                    report = json.load(f)
                    logging.debug(f"Pytest JSON report: {json.dumps(report, indent=2)}")
                    # Clean up the report file
                    try:
                        os.remove('.report.json')
                    except OSError:
                        pass
                    return {'runner': 'pytest', 'results': report}
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.error(f"Failed to read pytest report: {e}")
                logging.error("Make sure pytest-json-report is installed: pip install pytest-json-report")
                # If we can't read the report but have stderr, use that
                if result.stderr:
                    return {'runner': 'pytest', 'results': {'errors': [{'longrepr': result.stderr}]}}
                return None
        elif command.startswith('jest'):
            try:
                return {'runner': 'jest', 'results': json.loads(result.stdout)}
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse Jest output: {e}")
                return None
        elif command.startswith('vitest'):
            try:
                return {'runner': 'vitest', 'results': json.loads(result.stdout)}
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse Vitest output: {e}")
                return None
                
    except Exception as e:
        logging.error(f"Error running test command: {e}")
        return None

def extract_js_test_function(file_path: str, function_name: str) -> Optional[str]:
    """Extract a test function from a JavaScript/TypeScript file.
    
    Args:
        file_path: Path to the test file
        function_name: Name of the test function to extract
        
    Returns:
        String containing the test function code, or None if not found
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Simple regex to find test blocks
        # This is a basic implementation - might need AST parsing for more complex cases
        import re
        test_patterns = [
            # Jest/Vitest patterns
            rf"test\(['\"]?{function_name}['\"]?,\s*(?:async\s*)?\(?.*?\)?\s*=>\s*{{(.*?)}}\)",
            rf"test\(['\"]?{function_name}['\"]?,\s*(?:async\s*)?\(?.*?\)?\s*function.*?{{(.*?)}}\)",
            rf"it\(['\"]?{function_name}['\"]?,\s*(?:async\s*)?\(?.*?\)?\s*=>\s*{{(.*?)}}\)",
            rf"it\(['\"]?{function_name}['\"]?,\s*(?:async\s*)?\(?.*?\)?\s*function.*?{{(.*?)}}\)",
        ]
        
        for pattern in test_patterns:
            if match := re.search(pattern, content, re.DOTALL):
                # Get the full test declaration
                start = match.start()
                while start > 0 and content[start-1] not in ';\n':
                    start -= 1
                return content[start:match.end()]
                
        return None
    except Exception as e:
        logging.error(f"Failed to extract test function: {e}")
        return None

def parse_test_results(test_results: Dict) -> List[Dict[str, str]]:
    """Parse test results from different test runners.
    
    Args:
        test_results: Dictionary containing test runner and results
        
    Returns:
        List of failing test info dictionaries
    """
    # Handle raw pytest results (no runner field)
    if 'tests' in test_results and 'runner' not in test_results:
        test_results = {'runner': 'pytest', 'results': test_results}
    
    runner = test_results.get('runner')
    results = test_results.get('results', {})
    logging.debug(f"Parsing test results for runner: {runner}")
    
    if runner == 'pytest':
        failing_tests = []
        
        # Handle collection errors from collectors field
        for collector in results.get('collectors', []):
            if collector.get('outcome') == 'failed':
                logging.debug(f"Processing pytest collector error: {collector}")
                error_msg = collector.get('longrepr', '')
                file_path = collector.get('nodeid', '')
                
                if file_path:
                    failing_tests.append({
                        'file': file_path,
                        'function': 'collection_error',
                        'message': error_msg
                    })
        
        # Handle regular test failures
        for test in results.get('tests', []):
            logging.debug(f"Processing pytest test: {test.get('nodeid')} (outcome: {test.get('outcome')})")
            if test.get('outcome') in ('failed', 'error'):
                failing_tests.append({
                    'file': test['nodeid'].split('::')[0],
                    'function': test['nodeid'].split('::')[-1],
                    'message': test.get('call', {}).get('longrepr', '')
                })
        
        # Handle test failures that don't have a call section
        for test in results.get('tests', []):
            if test.get('outcome') in ('failed', 'error') and not test.get('call'):
                failing_tests.append({
                    'file': test['nodeid'].split('::')[0],
                    'function': test['nodeid'].split('::')[-1],
                    'message': test.get('longrepr', '')
                })
        
        logging.debug(f"Found {len(failing_tests)} failing pytest tests")
        return failing_tests
    elif runner == 'jest':
        failing_tests = []
        for test_result in results.get('testResults', []):
            file_path = test_result['name']
            for assertion in test_result.get('assertionResults', []):
                if assertion['status'] == 'failed':
                    failing_tests.append({
                        'file': file_path,
                        'function': assertion['title'],
                        'message': '\n'.join(assertion.get('failureMessages', []))
                    })
        return failing_tests
    elif runner == 'vitest':
        failing_tests = []
        for test_result in results.get('testResults', []):
            file_path = test_result['name']
            for task in test_result.get('tasks', []):
                if task['result'].get('state') == 'fail':
                    failing_tests.append({
                        'file': file_path,
                        'function': task['name'],
                        'message': task['result'].get('error', {}).get('message', '')
                    })
        return failing_tests
    else:
        return []

def extract_failing_tests(test_results: Dict, include_source: bool = False) -> List[Dict[str, str]]:
    """Extract code from failing tests.
    
    Args:
        test_results: Dictionary containing test results
        include_source: Whether to include related source code
        
    Returns:
        List of dictionaries containing test info and code
    """
    failing_tests = []
    logging.debug(f"Processing test results with include_source={include_source}")
    
    # Parse test results based on runner
    parsed_results = parse_test_results(test_results)
    logging.debug(f"Found {len(parsed_results)} failing tests to process")
    
    # Get the test directory from the root field in the test results
    test_root = test_results.get('results', {}).get('root')
    if not test_root and parsed_results:
        # Try to extract test root from error message
        first_test = parsed_results[0]
        error_msg = first_test.get('message', '')
        import re
        root_match = re.search(r"test module '([^']+)'", error_msg)
        if root_match:
            # Get the root directory of the project
            test_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(root_match.group(1)))))
            logging.debug(f"Extracted test root from error message: {test_root}")
    
    if not test_root:
        # Try to find the test directory from the command line arguments
        import sys
        for arg in sys.argv:
            if '../' in arg and os.path.exists(arg) and os.path.isdir(arg):
                test_root = os.path.abspath(arg)
                break
    
    if not test_root:
        logging.error("Could not determine test root directory")
        return []
    
    logging.debug(f"Using test root directory: {test_root}")
    
    for test in parsed_results:
        file_path = test['file']
        func_name = test['function']
        logging.debug(f"Processing failing test: {file_path}::{func_name}")
        
        # Convert relative path to absolute path if needed
        if not os.path.isabs(file_path):
            abs_path = os.path.abspath(os.path.join(test_root, file_path))
            if os.path.exists(abs_path):
                file_path = abs_path
            else:
                logging.warning(f"Could not find test file: {abs_path}")
                continue
        
        # Extract test code based on file type
        if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            code = extract_js_test_function(file_path, func_name)
        else:
            code = extract_test_function(file_path, func_name)
        
        if code:
            test_info = {
                'file': file_path,
                'function': func_name,
                'code': code,
                'message': test['message']
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
                
            failing_tests.append(test_info)
        else:
            logging.warning(f"Could not extract code for test: {file_path}::{func_name}")
    
    return failing_tests

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
            
        # For collection errors, return the entire file content
        if function_name == 'collection_error':
            return content
            
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
    
    # Group tests by error type
    collection_errors = []
    test_failures = []
    for test in failing_tests:
        if test['function'] == 'collection_error':
            collection_errors.append(test)
        else:
            test_failures.append(test)
    
    # Format collection errors first
    if collection_errors:
        output.append("### Collection Errors\n")
        for test in collection_errors:
            output.append(f"**{test['file']}**")
            output.append("```")
            output.append(test['message'])
            output.append("```\n")
    
    # Format test failures
    if test_failures:
        output.append("### Test Failures\n")
        for test in test_failures:
            output.append(f"**{test['file']}::{test['function']}**")
            output.append("```python")
            output.append(test['code'])
            output.append("```")
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