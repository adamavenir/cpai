"""Example test file to demonstrate source code integration."""

from cpai.source_analysis import analyze_test_file, extract_source_code
from cpai.test_utils import extract_test_function

def test_source_integration():
    """Test that demonstrates source code integration with a failing test."""
    # Get source files for this test file
    source_files = analyze_test_file(__file__)
    
    # Extract source code
    source_code = extract_source_code(source_files)
    
    # This assertion will fail to demonstrate both test code and source code output
    assert len(source_code) > 10, "Should find more source files" 