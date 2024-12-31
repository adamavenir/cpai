"""Tests for test extraction functionality."""

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from cpai.test_analysis.config import TestAnalysisConfig
from cpai.test_analysis.extractor import TestExtractor, TestLocation, TestFailure


@pytest.fixture
def config():
    """Create a test configuration."""
    return TestAnalysisConfig()


@pytest.fixture
def extractor(config):
    """Create a test extractor instance."""
    return TestExtractor(config)


def test_extract_test_function(extractor, tmp_path):
    """Test extracting a test function's source code."""
    test_file = tmp_path / "test_example.py"
    test_content = '''
def test_something():
    """Test something."""
    assert True

def test_another():
    assert False
'''
    test_file.write_text(test_content)
    
    # Extract first test
    source = extractor.extract_test_function(test_file, "test_something")
    assert source is not None
    assert 'def test_something():' in source
    assert '"""Test something."""' in source
    assert 'assert True' in source
    
    # Extract second test
    source = extractor.extract_test_function(test_file, "test_another")
    assert source is not None
    assert 'def test_another():' in source
    assert 'assert False' in source
    
    # Try non-existent test
    source = extractor.extract_test_function(test_file, "test_nonexistent")
    assert source is None


def test_extract_test_location(extractor):
    """Test extracting test location from pytest report."""
    # Mock a simple test report
    report = Mock()
    report.nodeid = "tests/test_example.py::test_something"
    report.location = ("tests/test_example.py", 42, "test_something")
    
    location = extractor._extract_test_location(report)
    assert location is not None
    assert location.file_path == Path("tests/test_example.py")
    assert location.line_number == 42
    assert location.function_name == "test_something"
    assert location.class_name is None
    
    # Test with class
    report.nodeid = "tests/test_example.py::TestClass::test_method"
    location = extractor._extract_test_location(report)
    assert location is not None
    assert location.class_name == "TestClass"
    assert location.function_name == "test_method"


def test_extract_failing_tests(extractor):
    """Test extracting information about failing tests."""
    # Mock pytest report with failures
    report = Mock()
    failure1 = Mock()
    failure1.nodeid = "tests/test_one.py::test_failed"
    failure1.location = ("tests/test_one.py", 10, "test_failed")
    failure1.longrepr = Mock()
    failure1.longrepr.reprcrash.path = "tests/test_one.py"
    failure1.longrepr.reprcrash.lineno = 10
    failure1.longrepr.reprcrash.message = "assertion failed"
    
    failure2 = Mock()
    failure2.nodeid = "tests/test_two.py::TestClass::test_method"
    failure2.location = ("tests/test_two.py", 20, "test_method")
    failure2.longrepr = "test failed"
    
    report.failed = [failure1, failure2]
    
    # Mock test function extraction
    with patch.object(extractor, 'extract_test_function', return_value="def test(): pass"):
        failures = extractor.extract_failing_tests(report)
        
    assert len(failures) == 2
    
    # Check first failure
    assert failures[0].location.file_path == Path("tests/test_one.py")
    assert failures[0].location.line_number == 10
    assert failures[0].location.function_name == "test_failed"
    assert "tests/test_one.py:10: assertion failed" in failures[0].traceback
    
    # Check second failure
    assert failures[1].location.file_path == Path("tests/test_two.py")
    assert failures[1].location.line_number == 20
    assert failures[1].location.function_name == "test_method"
    assert failures[1].location.class_name == "TestClass"
    assert failures[1].traceback == "test failed"


def test_function_caching(extractor, tmp_path):
    """Test that test function extraction uses caching."""
    test_file = tmp_path / "test_cache.py"
    test_file.write_text("def test_something():\n    assert True")
    
    # First call should read the file
    source1 = extractor.extract_test_function(test_file, "test_something")
    assert source1 is not None
    
    # Second call should use cache
    with patch('builtins.open', side_effect=Exception("Should not read file")):
        source2 = extractor.extract_test_function(test_file, "test_something")
        assert source2 == source1


def test_error_handling(extractor, tmp_path):
    """Test error handling in various scenarios."""
    # Test with non-existent file
    source = extractor.extract_test_function(Path("nonexistent.py"), "test")
    assert source is None
    
    # Test with invalid Python syntax
    bad_file = tmp_path / "bad_syntax.py"
    bad_file.write_text("def test_bad(): invalid python )")
    source = extractor.extract_test_function(bad_file, "test_bad")
    assert source is None
    
    # Test with invalid test report
    bad_report = Mock()
    del bad_report.nodeid  # Make nodeid attribute missing
    location = extractor._extract_test_location(bad_report)
    assert location is None


def test_silent_mode(tmp_path):
    """Test that silent mode suppresses logging."""
    # Create a config with silent mode
    config = TestAnalysisConfig(silent=True)
    extractor = TestExtractor(config)
    
    # Verify logger level is set to ERROR
    assert logging.getLogger('cpai.test_analysis.extractor').level == logging.ERROR
    
    # Create a config without silent mode
    config = TestAnalysisConfig(silent=False)
    extractor = TestExtractor(config)
    
    # Verify logger level is set to INFO
    assert logging.getLogger('cpai.test_analysis.extractor').level == logging.INFO 