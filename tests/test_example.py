"""Example test file to demonstrate source code integration."""

from cpai.source_analysis import extract_imports, find_source_file, get_search_paths
from cpai.test_utils import extract_test_function

def test_complex_source_integration():
    """Test that demonstrates integration with multiple source files."""
    # Get search paths for a test file
    paths = get_search_paths(__file__)
    
    # Try to find a source file using the full module path
    source_file = find_source_file("cpai.test_utils", paths)
    assert source_file is not None, "Should find the source file"
    
    # Extract test function (should return None for non-existent function)
    test_code = extract_test_function(source_file, "nonexistent_function")
    assert test_code is None, "Should not find a non-existent function"