"""Tests for source code analysis functionality."""

import os
import tempfile
import shutil
from pathlib import Path
from cpai.source_analysis import (
    extract_imports,
    find_source_file,
    get_search_paths,
    analyze_test_file,
    extract_source_code
)

def test_extract_imports():
    """Test extraction of imports from Python files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / 'test_example.py'
        test_content = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
from .utils import helper
from ..core import main
'''
        test_file.write_text(test_content)
        
        imports = extract_imports(str(test_file))
        assert 'os' in imports
        assert 'sys' in imports
        assert 'pathlib' in imports
        assert 'typing' in imports
        assert 'utils' in imports
        assert 'core' in imports

def test_find_source_file():
    """Test finding source files for modules."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source files
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        
        # Single file module
        (src_dir / 'utils.py').write_text('def helper(): pass')
        
        # Package module
        pkg_dir = src_dir / 'core'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').write_text('from .main import *')
        (pkg_dir / 'main.py').write_text('def main(): pass')
        
        # Test finding single file module
        source_file = find_source_file('utils', [str(src_dir)])
        assert source_file == str(src_dir / 'utils.py')
        
        # Test finding package module
        source_file = find_source_file('core', [str(src_dir)])
        assert source_file == str(pkg_dir / '__init__.py')

def test_get_search_paths():
    """Test getting search paths for source files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        test_dir = Path(temp_dir) / 'tests'
        test_dir.mkdir()
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        lib_dir = Path(temp_dir) / 'lib'
        lib_dir.mkdir()
        
        test_file = test_dir / 'test_example.py'
        test_file.write_text('def test_example(): pass')
        
        paths = get_search_paths(str(test_file))
        
        # Should include test directory
        assert str(test_dir) in paths
        # Should include parent directory
        assert str(test_dir.parent) in paths
        # Should include src directory
        assert str(src_dir) in paths
        # Should include lib directory
        assert str(lib_dir) in paths

def test_analyze_test_file():
    """Test analyzing test files for source dependencies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source files
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        (src_dir / 'utils.py').write_text('def helper(): pass')
        (src_dir / 'main.py').write_text('def main(): pass')
        
        # Create test file
        test_dir = Path(temp_dir) / 'tests'
        test_dir.mkdir()
        test_file = test_dir / 'test_main.py'
        test_content = '''
from src.utils import helper
from src.main import main

def test_main():
    helper()
    main()
'''
        test_file.write_text(test_content)
        
        source_files = analyze_test_file(str(test_file), test_mode=True)
        assert 'src.utils' in source_files
        assert 'src.main' in source_files
        assert source_files['src.utils'].endswith('utils.py')
        assert source_files['src.main'].endswith('main.py')

def test_extract_source_code():
    """Test extracting code from source files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source files
        utils_file = Path(temp_dir) / 'utils.py'
        utils_content = 'def helper(): pass'
        utils_file.write_text(utils_content)
        
        main_file = Path(temp_dir) / 'main.py'
        main_content = 'def main(): pass'
        main_file.write_text(main_content)
        
        source_files = {
            'utils': str(utils_file),
            'main': str(main_file)
        }
        
        source_code = extract_source_code(source_files)
        assert 'utils' in source_code
        assert source_code['utils'] == utils_content
        assert 'main' in source_code
        assert source_code['main'] == main_content 