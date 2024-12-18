"""Tests for test execution and code extraction functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from cpai.test_utils import (
    extract_test_function,
    parse_nodeid,
    extract_failing_tests,
    format_test_output
)

def test_parse_nodeid():
    """Test parsing of pytest nodeids."""
    # Simple case
    file_path, func_name = parse_nodeid('tests/test_main.py::test_function')
    assert file_path == 'tests/test_main.py'
    assert func_name == 'test_function'
    
    # With class
    file_path, func_name = parse_nodeid('tests/test_main.py::TestClass::test_method')
    assert file_path == 'tests/test_main.py'
    assert func_name == 'test_method'

def test_extract_test_function():
    """Test extraction of test function code."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / 'test_example.py'
        test_content = '''
def setup_function():
    pass

def test_success():
    assert True

def test_failure():
    x = 1
    y = 2
    assert x == y, "x should equal y"
'''
        test_file.write_text(test_content)
        
        # Test extracting existing function
        code = extract_test_function(str(test_file), 'test_failure')
        assert code is not None
        assert 'x = 1' in code
        assert 'y = 2' in code
        assert 'assert x == y' in code
        
        # Test non-existent function
        code = extract_test_function(str(test_file), 'test_nonexistent')
        assert code is None

def test_extract_failing_tests():
    """Test extraction of failing test information."""
    # Mock test results
    test_results = {
        'tests': [
            {
                'nodeid': 'tests/test_example.py::test_success',
                'outcome': 'passed'
            },
            {
                'nodeid': 'tests/test_example.py::test_failure',
                'outcome': 'failed',
                'call': {
                    'longrepr': 'AssertionError: x should equal y'
                }
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / 'tests' / 'test_example.py'
        test_file.parent.mkdir(parents=True)
        test_content = '''
def test_success():
    assert True

def test_failure():
    x = 1
    y = 2
    assert x == y, "x should equal y"
'''
        test_file.write_text(test_content)
        
        # Update test results with correct path
        test_results['tests'][0]['nodeid'] = f'{test_file}::test_success'
        test_results['tests'][1]['nodeid'] = f'{test_file}::test_failure'
        
        failing_tests = extract_failing_tests(test_results)
        assert len(failing_tests) == 1
        assert failing_tests[0]['function'] == 'test_failure'
        assert 'x = 1' in failing_tests[0]['code']
        assert 'AssertionError' in failing_tests[0]['message']

def test_format_test_output():
    """Test formatting of test output."""
    failing_tests = [
        {
            'file': 'tests/test_example.py',
            'function': 'test_failure',
            'code': 'def test_failure():\n    assert False',
            'message': 'AssertionError'
        }
    ]
    
    output = format_test_output(failing_tests)
    assert '## Failing Tests' in output
    assert '### tests/test_example.py::test_failure' in output
    assert '```python' in output
    assert 'def test_failure()' in output
    assert '#### Error Message' in output
    assert 'AssertionError' in output

def test_format_test_output_no_failures():
    """Test formatting output when no tests failed."""
    output = format_test_output([])
    assert output == "No failing tests found." 