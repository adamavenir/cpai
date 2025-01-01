"""Tests for source code analysis functionality."""

import pytest
import logging
import sys
from pathlib import Path
from cpai.test_analysis.config import TestAnalysisConfig
from cpai.test_analysis.source_analyzer import SourceAnalyzer, SourceLocation, SourceContext

# Configure logging for tests
logger = logging.getLogger('cpai.test_analysis.source_analyzer')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@pytest.fixture
def config():
    """Create a test configuration."""
    config = TestAnalysisConfig()
    config.workspace_dir = None  # Explicitly initialize to None
    return config


@pytest.fixture
def analyzer(config):
    """Create a source analyzer instance."""
    return SourceAnalyzer(config)


def test_analyzer_initialization(analyzer):
    """Test that analyzer initializes correctly."""
    assert isinstance(analyzer._cache, dict)


def test_find_source_file(analyzer, tmp_path):
    """Test finding source files."""
    # Create a test module
    module_dir = tmp_path / "mymodule"
    module_dir.mkdir()
    (module_dir / "__init__.py").touch()
    source_file = module_dir / "source.py"
    source_file.write_text("def test_func(): pass")
    
    # Test finding package module
    found_path = analyzer.find_source_file("mymodule")
    assert found_path is None  # Should be None since not in Python path
    
    # Test with workspace dir
    analyzer.config.workspace_dir = str(tmp_path)
    found_path = analyzer.find_source_file("mymodule")
    assert found_path == module_dir / "__init__.py"
    
    # Test finding submodule
    found_path = analyzer.find_source_file("mymodule.source")
    assert found_path == source_file


def test_extract_imports(analyzer, tmp_path):
    """Test extracting imports from a source file."""
    test_file = tmp_path / "test_imports.py"
    test_content = '''
import os
import sys as system
from pathlib import Path
from typing import List, Optional
from mymodule import MyClass
from . import utils
from .helpers import helper1, helper2

def test_func():
    pass
'''
    test_file.write_text(test_content)
    
    imports = analyzer.extract_imports(test_file)
    assert set(imports) == {'os', 'sys', 'pathlib', 'typing', 'mymodule'}


def test_analyze_dependencies(analyzer, tmp_path):
    """Test analyzing dependencies recursively."""
    # Create test files
    module_a = tmp_path / "module_a.py"
    module_b = tmp_path / "module_b.py"
    module_c = tmp_path / "module_c.py"
    
    module_a.write_text('''
import module_b
from module_c import func
''')
    
    module_b.write_text('''
import module_c
''')
    
    module_c.write_text('''
def func():
    pass
''')
    
    analyzer.config.workspace_dir = str(tmp_path)
    deps = analyzer.analyze_dependencies(module_a)
    assert 'module_b' in deps
    assert 'module_c' in deps


def test_get_source_context(analyzer, tmp_path):
    """Test getting source context around a line."""
    test_file = tmp_path / "test_context.py"
    test_content = '''
import os
import sys

def func_a():
    pass

def func_b():
    return True

def func_c():
    return False
'''
    test_file.write_text(test_content)
    
    context = analyzer.get_source_context(test_file, 5, context_lines=2)
    assert context is not None
    assert context.location.line_number == 3
    assert context.location.end_line_number == 7
    assert 'func_a' in context.source_code
    assert set(context.imports) == {'os', 'sys'}


def test_error_handling(analyzer):
    """Test error handling for invalid files."""
    nonexistent = Path("nonexistent.py")
    
    # Should return None/empty collections instead of raising exceptions
    assert analyzer.find_source_file("nonexistent") is None
    assert analyzer.extract_imports(nonexistent) == []
    assert analyzer.analyze_dependencies(nonexistent) == set()
    assert analyzer.get_source_context(nonexistent, 1) is None


def test_caching(analyzer, tmp_path):
    """Test that results are properly cached."""
    test_file = tmp_path / "test_cache.py"
    test_content = '''
import os

def func():
    pass
'''
    test_file.write_text(test_content)
    
    # First calls should read the file
    imports1 = analyzer.extract_imports(test_file)
    context1 = analyzer.get_source_context(test_file, 1)
    
    # Delete the file to ensure second calls use cache
    test_file.unlink()
    
    # Second calls should use cache
    imports2 = analyzer.extract_imports(test_file)
    context2 = analyzer.get_source_context(test_file, 1)
    
    assert imports1 == imports2
    assert context1 == context2 