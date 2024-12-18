import os
import tempfile
import shutil
import unittest
from pathlib import Path
from cpai.main import get_files, run_test_command, process_test_results
from cpai.constants import DEFAULT_EXCLUDE_PATTERNS
import json
from unittest.mock import patch, mock_open

class TestGetFiles(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create some test files and directories
        self.create_test_files()

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    def create_test_files(self):
        """Create a test directory structure."""
        # Create Python files
        Path(self.test_dir, "main.py").write_text("def main(): pass")
        Path(self.test_dir, "__init__.py").write_text("")
        Path(self.test_dir, "constants.py").write_text("VERSION = '1.0.0'")
        
        # Create a subdirectory with files
        subdir = Path(self.test_dir, "subdir")
        subdir.mkdir()
        Path(subdir, "module.py").write_text("def func(): pass")
        
        # Create files that should be excluded
        pycache_dir = Path(self.test_dir, "__pycache__")
        pycache_dir.mkdir()
        Path(pycache_dir, "main.cpython-39.pyc").write_text("")
        
        # Create test files (should be excluded by default)
        test_dir = Path(self.test_dir, "tests")
        test_dir.mkdir()
        Path(test_dir, "test_main.py").write_text("def test_main(): pass")
        
        # Create config files
        Path(self.test_dir, "setup.py").write_text("from setuptools import setup")
        Path(self.test_dir, "requirements.txt").write_text("pathspec==0.11.0")

    def test_get_files_basic(self):
        """Test basic file filtering with default configuration."""
        config = {
            'include': ['.'],
            'fileExtensions': ['.py']  # Only process Python files
        }
        files = get_files(self.test_dir, config)

        # Convert absolute paths to relative for comparison
        rel_files = [os.path.relpath(f, self.test_dir) for f in files]

        # Should include Python files in root and subdirectories
        expected = {
            "main.py",
            "__init__.py",
            "constants.py",
            os.path.join("subdir", "module.py")
        }
        self.assertEqual(set(rel_files), expected)

    def test_get_files_with_absolute_path(self):
        """Test that get_files works correctly with absolute paths."""
        abs_path = os.path.abspath(self.test_dir)
        files = get_files(abs_path)

        # All returned paths should be absolute
        self.assertTrue(all(os.path.isabs(f) for f in files))

    def test_get_files_with_relative_path(self):
        """Test that get_files works correctly with relative paths."""
        # Get current directory
        current_dir = os.getcwd()
        try:
            # Change to parent of test directory
            os.chdir(os.path.dirname(self.test_dir))
            # Use relative path
            rel_path = os.path.basename(self.test_dir)
            files = get_files(rel_path)

            # All returned paths should be absolute
            self.assertTrue(all(os.path.isabs(f) for f in files))
            self.assertTrue(all(os.path.exists(f) for f in files))
        finally:
            # Restore current directory
            os.chdir(current_dir)

    def test_get_files_exclude_patterns(self):
        """Test that exclude patterns work correctly."""
        # Create a custom exclude pattern
        config = {
            'exclude': ['**/subdir/**']  # Exclude the subdir directory
        }
        
        files = get_files(self.test_dir, config=config)
        rel_files = [os.path.relpath(f, self.test_dir) for f in files]
        
        # Should not include files from subdir
        self.assertFalse(any("subdir" in f for f in rel_files))

    def test_get_files_include_patterns(self):
        """Test that include patterns work correctly."""
        # Create a custom include pattern
        config = {
            'include': ['**/subdir/**'],  # Only include files in subdir
            'fileExtensions': ['.py']  # Only process Python files
        }
        
        files = get_files(self.test_dir, config=config)
        rel_files = [os.path.relpath(f, self.test_dir) for f in files]
        
        # Should only include files from subdir
        self.assertTrue(all("subdir" in f for f in rel_files))

    def test_get_files_symlinks(self):
        """Test that symlinks are handled correctly."""
        config = {
            'include': ['.'],
            'fileExtensions': ['.py']  # Only process Python files
        }
        
        # Create a symlink to a Python file
        source = Path(self.test_dir, "main.py")
        link = Path(self.test_dir, "main_link.py")
        os.symlink(source, link)
        
        try:
            files = get_files(self.test_dir, config)
            rel_files = [os.path.relpath(f, self.test_dir) for f in files]
            
            # Should include both the original file and the symlink
            self.assertTrue(any("main.py" in f for f in rel_files))
            self.assertTrue(any("main_link.py" in f for f in rel_files))
        finally:
            # Cleanup
            if os.path.exists(link):
                os.remove(link)

    def test_get_files_broken_symlinks(self):
        """Test that broken symlinks are handled gracefully."""
        # Create a broken symlink
        nonexistent = Path(self.test_dir, "nonexistent.py")
        link = Path(self.test_dir, "broken_link.py")
        os.symlink(nonexistent, link)
        
        # Should not raise an exception
        files = get_files(self.test_dir)
        rel_files = [os.path.relpath(f, self.test_dir) for f in files]
        
        # Should not include the broken symlink
        self.assertFalse("broken_link.py" in rel_files)

    def test_run_test_command_pytest(self):
        """Test running pytest command."""
        mock_report = {
            'tests': [
                {
                    'nodeid': 'tests/test_example.py::test_success',
                    'outcome': 'passed'
                }
            ]
        }
        
        # Mock both the subprocess run and file read
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_report))):
            
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test output"
            
            result = run_test_command('pytest')
            
            # Verify pytest was called with json-report flag
            mock_run.assert_called_once()
            command = mock_run.call_args[0][0]
            assert '--json-report' in command
            
            # Verify report was read
            assert result == mock_report

    def test_run_test_command_pytest_no_report(self):
        """Test handling missing json report."""
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', side_effect=FileNotFoundError):
            
            mock_run.return_value.returncode = 0
            result = run_test_command('pytest')
            
            assert result is None

    def test_run_test_command_other(self):
        """Test running non-pytest command."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test output"
            mock_run.return_value.stderr = ""
            
            result = run_test_command('other_test_command')
            
            # Verify command was run as-is
            mock_run.assert_called_once()
            assert result == {'output': 'Test output', 'error': ''}

    def test_process_test_results(self):
        """Test processing of test results."""
        test_results = {
            'tests': [
                {
                    'nodeid': 'tests/test_example.py::test_failure',
                    'outcome': 'failed',
                    'call': {
                        'longrepr': 'AssertionError: test failed'
                    }
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / 'tests' / 'test_example.py'
            test_file.parent.mkdir(parents=True)
            test_content = '''
def test_failure():
    assert False, "test failed"
'''
            test_file.write_text(test_content)
            
            # Update test results with correct path
            test_results['tests'][0]['nodeid'] = f'{test_file}::test_failure'
            
            output = process_test_results(test_results)
            assert output is not None
            assert 'test_failure' in output
            assert 'assert False' in output
            assert 'AssertionError' in output

    def test_process_test_results_no_failures(self):
        """Test processing results with no failures."""
        test_results = {
            'tests': [
                {
                    'nodeid': 'tests/test_example.py::test_success',
                    'outcome': 'passed'
                }
            ]
        }
        
        output = process_test_results(test_results)
        assert output == "No failing tests found."

if __name__ == '__main__':
    unittest.main()
