"""Tests for test parsing functionality."""

import pytest
from pathlib import Path
from cpai.test_analysis.config import TestAnalysisConfig
from cpai.test_analysis.parser import TestParser, TestDefinition, TestDependency


@pytest.fixture
def config():
    """Create a test configuration."""
    return TestAnalysisConfig()


@pytest.fixture
def parser(config):
    """Create a parser instance."""
    return TestParser(config)


def test_parser_initialization(parser):
    """Test that parser initializes correctly."""
    assert isinstance(parser._cache, dict)


def test_parse_test_file(parser, tmp_path):
    """Test parsing a test file."""
    test_file = tmp_path / "test_example.py"
    test_content = '''
import pytest

@pytest.fixture
def my_fixture():
    return "test"

def test_something():
    """Test something."""
    assert True

class TestClass:
    def test_method(self):
        assert True
    
    async def test_async(self):
        assert True

def not_a_test():
    pass
'''
    test_file.write_text(test_content)
    
    test_defs = parser.parse_test_file(test_file)
    assert len(test_defs) == 3
    
    # Check standalone test
    standalone = next(t for t in test_defs if t.name == 'test_something')
    assert standalone.docstring == "Test something."
    assert not standalone.class_name
    assert not standalone.is_async
    
    # Check class test method
    method = next(t for t in test_defs if t.name == 'test_method')
    assert method.class_name == 'TestClass'
    assert not method.is_async
    
    # Check async test method
    async_method = next(t for t in test_defs if t.name == 'test_async')
    assert async_method.class_name == 'TestClass'
    assert async_method.is_async


def test_extract_dependencies(parser, tmp_path):
    """Test extracting dependencies from a test file."""
    test_file = tmp_path / "test_deps.py"
    test_content = '''
import pytest
import os.path
from pathlib import Path
from typing import List, Optional
from mymodule import MyClass
from . import utils
from .helpers import helper1, helper2

def test_something():
    assert True
'''
    test_file.write_text(test_content)
    
    deps = parser.extract_dependencies(test_file)
    assert len(deps) == 7
    
    # Check regular imports
    pytest_import = next(d for d in deps if d.module_name == 'pytest')
    assert not pytest_import.is_from_import
    
    os_import = next(d for d in deps if d.module_name == 'os.path')
    assert not os_import.is_from_import
    
    # Check from imports
    path_import = next(d for d in deps if d.module_name == 'pathlib')
    assert path_import.is_from_import
    assert path_import.imported_names == ['Path']
    
    typing_import = next(d for d in deps if d.module_name == 'typing')
    assert typing_import.is_from_import
    assert set(typing_import.imported_names) == {'List', 'Optional'}
    
    mymodule_import = next(d for d in deps if d.module_name == 'mymodule')
    assert mymodule_import.is_from_import
    assert mymodule_import.imported_names == ['MyClass']
    
    utils_import = next(d for d in deps if d.module_name == '')
    assert utils_import.is_from_import
    assert utils_import.imported_names == ['utils']
    
    helpers_import = next(d for d in deps if d.module_name == '.helpers')
    assert helpers_import.is_from_import
    assert set(helpers_import.imported_names) == {'helper1', 'helper2'}


def test_get_test_fixtures(parser, tmp_path):
    """Test extracting fixtures from a test file."""
    test_file = tmp_path / "test_fixtures.py"
    test_content = '''
import pytest

@pytest.fixture
def my_fixture():
    return "test"

@pytest.fixture
def another_fixture():
    return 42

def test_with_fixtures(my_fixture, tmp_path):
    assert my_fixture == "test"

class TestClass:
    def test_method(self, another_fixture):
        assert another_fixture == 42
'''
    test_file.write_text(test_content)
    
    fixtures = parser.get_test_fixtures(test_file)
    assert fixtures == {'my_fixture', 'another_fixture', 'tmp_path'}


def test_parse_invalid_file(parser, tmp_path):
    """Test parsing an invalid Python file."""
    test_file = tmp_path / "invalid.py"
    test_file.write_text("def invalid syntax")
    
    # Should return empty lists/sets instead of raising exceptions
    assert parser.parse_test_file(test_file) == []
    assert parser.extract_dependencies(test_file) == []
    assert parser.get_test_fixtures(test_file) == set()


def test_parse_nonexistent_file(parser):
    """Test parsing a nonexistent file."""
    file_path = Path("nonexistent.py")
    
    # Should return empty lists/sets instead of raising exceptions
    assert parser.parse_test_file(file_path) == []
    assert parser.extract_dependencies(file_path) == []
    assert parser.get_test_fixtures(file_path) == set()


def test_caching(parser, tmp_path):
    """Test that results are properly cached."""
    test_file = tmp_path / "test_cache.py"
    test_content = '''
def test_something():
    assert True
'''
    test_file.write_text(test_content)
    
    # First call should read the file
    test_defs1 = parser.parse_test_file(test_file)
    deps1 = parser.extract_dependencies(test_file)
    fixtures1 = parser.get_test_fixtures(test_file)
    
    # Delete the file to ensure second call uses cache
    test_file.unlink()
    
    # Second call should use cache
    test_defs2 = parser.parse_test_file(test_file)
    deps2 = parser.extract_dependencies(test_file)
    fixtures2 = parser.get_test_fixtures(test_file)
    
    assert test_defs1 == test_defs2
    assert deps1 == deps2
    assert fixtures1 == fixtures2 