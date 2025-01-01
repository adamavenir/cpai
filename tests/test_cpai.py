import unittest
import os
import tempfile
import shutil
import json
import argparse
import logging
import subprocess
from unittest.mock import patch, MagicMock, ANY
from cpai.main import (
    read_config,
    get_files,
    format_content,
    write_output,
    cpai,
    main,
    configure_logging,
)
from cpai.constants import DEFAULT_EXCLUDE_PATTERNS, DEFAULT_CHUNK_SIZE
from cpai.content_size import validate_content_size
from cpai.formatter import format_tree
from cpai.progress import ProgressIndicator
import tiktoken
import time

class TestCPAI(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directories
        os.makedirs('src')
        os.makedirs('custom')
        os.makedirs(os.path.join('test_samples', 'python', 'services'))
        
        # Create test files
        with open('src/test.py', 'w') as f:
            f.write('def test_func():\n    pass\n')
        with open('src/utils.py', 'w') as f:
            f.write('def util_func():\n    pass\n')
        with open('custom/custom.py', 'w') as f:
            f.write('def custom_func():\n    pass\n')
        with open('custom/test.py', 'w') as f:
            f.write('def test_func():\n    pass\n')
        with open('settings.json', 'w') as f:
            f.write('{"setting": "value"}\n')
            
        # Create .gitignore file
        with open('.gitignore', 'w') as f:
            f.write('temp/\n!temp/keep.txt\n')
            
        # Create temp directory with files
        os.makedirs('temp')
        with open('temp/ignore.txt', 'w') as f:
            f.write('ignore me\n')
        with open('temp/keep.txt', 'w') as f:
            f.write('keep me\n')

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_read_config_with_custom_config(self):
        """Test reading custom configuration file"""
        config_data = {
            "include": ["src"],
            "fileExtensions": [".py"],
            "chunkSize": 50000,
            "outputFile": True
        }
        with open('cpai.config.json', 'w') as f:
            json.dump(config_data, f)
        
        config = read_config()
        self.assertEqual(config['fileExtensions'], [".py"])
        self.assertEqual(config['chunkSize'], 50000)
        # Don't test include as it gets merged with defaults

    def test_write_output_to_file(self):
        """Test writing output to file"""
        config = {
            'outputFile': 'test_output.md',
            'usePastebin': False,
            'chunkSize': 1000,
            'files': ['src/main.py']
        }
        content = "Test content"
        
        write_output(content, config)
        
        self.assertTrue(os.path.exists('test_output.md'))
        with open('test_output.md', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_write_output_to_clipboard(self):
        """Test copying output to clipboard"""
        config = {
            'outputFile': False,
            'usePastebin': True,
            'chunkSize': 1000,
            'files': ['src/main.py']
        }
        content = "Test content"
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            write_output(content, config)
            
            mock_popen.assert_called_once_with(['pbcopy'], stdin=subprocess.PIPE)
            mock_process.communicate.assert_called_once_with(content.encode('utf-8'))

    def test_cpai_with_directory(self):
        """Test cpai function with directory input"""
        # Create a test file in src directory
        os.makedirs('src', exist_ok=True)
        with open('src/test.py', 'w') as f:
            f.write('def test():\n    pass\n')
    
        cli_options = {
            'outputFile': False,
            'usePastebin': False,
            'include_all': False,
            'fileExtensions': ['.py']  # Only process Python files
        }
    
        try:
            with patch('cpai.main.write_output') as mock_write:
                result = cpai(['src'], cli_options)
                self.assertIsNotNone(result)  # Check that we got some content
        except Exception as e:
            self.fail(f"cpai() raised {type(e).__name__} unexpectedly!")

    def test_cpai_with_specific_files(self):
        """Test cpai function with specific file inputs"""
        test_dir = os.path.join('test_samples', 'python', 'services')
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, 'test_service.py')
        with open(test_file, 'w') as f:
            f.write('def test_func():\n    pass\n')
    
        cli_options = {
            'outputFile': False,
            'usePastebin': False,
            'fileExtensions': ['.py']
        }
    
        with patch('cpai.main.write_output') as mock_write:
            cpai([test_file], cli_options)
            mock_write.assert_called_once()
            self.assertEqual(len(mock_write.call_args[0][1]['files']), 1)

    def test_get_files_with_config_patterns(self):
        """Test get_files with custom config patterns"""
        config = {
            'include': ['src/**/*.py'],  # Only include Python files in src
            'exclude': ['**/test.py']    # Exclude test files
        }
        
        files = get_files('src', config)
        self.assertTrue(any('utils.py' in f for f in files))  # utils.py should be included
        self.assertFalse(any('test.py' in f for f in files))  # test.py should be excluded

    def test_get_files_with_custom_extensions(self):
        """Test get_files with custom file extensions"""
        config = {
            'fileExtensions': ['.py']  # Only include Python files
        }
        
        files = get_files('src', config)
        self.assertTrue(all(f.endswith('.py') for f in files))  # All files should be Python files

    def test_get_files_with_gitignore(self):
        """Test get_files respects .gitignore patterns"""
        config = {
            'include_all': False  # Respect .gitignore
        }
        
        files = get_files('.', config)
        self.assertIn('temp/keep.txt', [os.path.normpath(f) for f in files])  # keep.txt should be included
        self.assertNotIn('temp/ignore.txt', [os.path.normpath(f) for f in files])  # ignore.txt should be excluded

    def test_read_config_with_invalid_config(self):
        """Test reading invalid configuration file"""
        config_data = {
            "include": "."  # Invalid: should be a list
        }
        with open('cpai.config.json', 'w') as f:
            json.dump(config_data, f)
        
        config = read_config()
        self.assertEqual(config['include'], ['**/*'])  # Should use default

    def test_read_config_with_invalid_fields(self):
        """Test reading config with invalid field values"""
        config_data = {
            "include": ".",  # Invalid: should be a list
            "chunkSize": "1000",  # Invalid: should be an integer
            "outputFile": 123  # Invalid: should be bool or string
        }
        with open('cpai.config.json', 'w') as f:
            json.dump(config_data, f)
        
        config = read_config()
        self.assertEqual(config['include'], ['**/*'])  # Should use default
        self.assertEqual(config['chunkSize'], DEFAULT_CHUNK_SIZE)  # Should use default
        self.assertFalse(config['outputFile'])  # Should use default

    def test_main_function_args(self):
        """Test main function argument parsing"""
        test_args = ['src/', '-f', 'output.md', '--debug']
        with patch('sys.argv', ['cpai'] + test_args):
            with patch('cpai.main.cpai') as mock_cpai:
                main()
                mock_cpai.assert_called_once()
                cli_options = mock_cpai.call_args[0][1]
                self.assertEqual(cli_options['outputFile'], 'output.md')

    def test_configure_logging(self):
        """Test logging configuration"""
        with self.assertLogs(level='DEBUG') as log:
            configure_logging(True)
            logging.debug("Test debug message")
            self.assertIn("DEBUG:root:Test debug message", log.output[0])

    def test_format_tree_complex(self):
        """Test tree formatting with complex directory structure"""
        files = [
            'src/main.py',
            'src/utils/helper.py',
            'src/utils/format.py',
            'config/settings.json'
        ]
        tree_output = format_tree(files)
        self.assertIn('src', tree_output)
        self.assertIn('utils', tree_output)
        self.assertIn('config', tree_output)
        self.assertIn('├──', tree_output)  # Check for tree characters
        self.assertIn('└──', tree_output)

    def test_cpai_with_no_args(self):
        """Test that running cpai with no arguments uses the current directory."""
        # Create a test file in the current directory
        with open('test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        
        try:
            # Call cpai with no arguments
            result = cpai([], {})
            
            # Verify that the file was processed
            self.assertIsNotNone(result)
            self.assertIn('test.py', result)
        finally:
            # Clean up
            os.remove('test.py')

    def test_bydir_with_explicit_dirs(self):
        """Test --bydir with explicitly specified directories."""
        # Create test directories
        os.makedirs('src/module1', exist_ok=True)
        os.makedirs('src/module2', exist_ok=True)
        with open('src/module1/test1.py', 'w') as f:
            f.write('def test1():\n    pass\n')
        with open('src/module2/test2.py', 'w') as f:
            f.write('def test2():\n    pass\n')
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/module1', 'src/module2'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            # Should be called twice, once for each directory
            self.assertEqual(mock_write.call_count, 2)
            # Check output filenames
            output_files = [call[0][1]['outputFile'] for call in mock_write.call_args_list]
            self.assertIn('module1.tree.md', [os.path.basename(f) for f in output_files])
            self.assertIn('module2.tree.md', [os.path.basename(f) for f in output_files])

    def test_bydir_auto_discovery(self):
        """Test --bydir without specified directories."""
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['.'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            # Should process both module1 and module2
            self.assertGreaterEqual(mock_write.call_count, 2)

    def test_bydir_overwrite_protection(self):
        """Test --bydir respects overwrite protection."""
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/module1'],
            'tree': True,
            'outputFile': True,
            'overwrite': False
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            # Should not write anything since file exists and overwrite is False
            mock_write.assert_not_called()

    def test_bydir_with_overwrite(self):
        """Test --bydir with overwrite enabled."""
        # Create test directory and file
        os.makedirs('src/module1', exist_ok=True)
        with open('src/module1/test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/module1'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            # Should write even though file exists
            mock_write.assert_called_once()

    def test_progress_indicator(self):
        """Test progress indicator functionality."""
        message = "Testing"
        progress = ProgressIndicator(message)

        with patch('sys.stdout.write') as mock_write:
            progress.start()
            # Give it time to make at least one update
            time.sleep(1)
            progress.stop()

            # Should have written to stdout at least once
            mock_write.assert_called()
            # Should have cleared the line at the end
            self.assertEqual(
                mock_write.call_args_list[-2][0][0],
                '\r' + ' ' * (len(message) + 3)
            )
            self.assertEqual(
                mock_write.call_args_list[-1][0][0],
                '\r'
            )

    def test_progress_indicator_in_cpai(self):
        """Test progress indicator is used in cpai function."""
        cli_options = {
            'outputFile': 'test_output.md',
            'tree': True
        }
        
        with patch('cpai.main.ProgressIndicator') as MockProgress:
            mock_progress = MagicMock()
            MockProgress.return_value = mock_progress
            
            cpai(['src/module1'], cli_options)
            
            # Progress indicator should be created and used
            MockProgress.assert_called_once()
            mock_progress.start.assert_called_once()
            mock_progress.stop.assert_called_once()

    def test_bydir_nested_paths(self):
        """Test --bydir handles nested paths correctly."""
        # Create nested test structure
        os.makedirs('src/nested/module1', exist_ok=True)
        os.makedirs('src/nested/module2', exist_ok=True)
        with open('src/nested/module1/test1.py', 'w') as f:
            f.write('def test1():\n    pass\n')
        with open('src/nested/module2/test2.py', 'w') as f:
            f.write('def test2():\n    pass\n')
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/nested/module1', 'src/nested/module2'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        original_cwd = os.getcwd()
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            
            # Should be called twice, once for each directory
            self.assertEqual(mock_write.call_count, 2)
            
            # Check output filenames are in original directory
            output_files = [call[0][1]['outputFile'] for call in mock_write.call_args_list]
            self.assertTrue(all(os.path.dirname(f) == original_cwd for f in output_files))
            self.assertIn('module1.tree.md', [os.path.basename(f) for f in output_files])
            self.assertIn('module2.tree.md', [os.path.basename(f) for f in output_files])

    def test_bydir_maintains_cwd(self):
        """Test --bydir maintains original working directory even after errors."""
        os.makedirs('src/error_module', exist_ok=True)
        original_cwd = os.getcwd()
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/error_module'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.process_files') as mock_process:
            # Simulate an error during processing
            mock_process.side_effect = Exception("Test error")
            
            cpai([], cli_options)
            
            # Should return to original directory
            self.assertEqual(os.getcwd(), original_cwd)

    def test_bydir_auto_discovery_excludes_hidden(self):
        """Test --bydir auto-discovery excludes hidden directories."""
        # Create test directories including hidden ones
        os.makedirs('src/visible_module', exist_ok=True)
        os.makedirs('.hidden_module', exist_ok=True)
        os.makedirs('src/.hidden_nested', exist_ok=True)
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['.'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            
            # Check output filenames don't include hidden directories
            output_files = [os.path.basename(call[0][1]['outputFile']) for call in mock_write.call_args_list]
            self.assertNotIn('.hidden_module.tree.md', output_files)
            self.assertNotIn('.hidden_nested.tree.md', output_files)

    def test_bydir_relative_file_paths(self):
        """Test --bydir handles relative file paths correctly."""
        # Create test structure
        os.makedirs('src/module1/nested', exist_ok=True)
        with open('src/module1/nested/test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/module1'],
            'tree': True,
            'outputFile': True,
            'overwrite': True
        }
        
        with patch('cpai.main.process_files') as mock_process:
            cpai([], cli_options)
            
            # Check that files are processed with correct relative paths
            processed_files = mock_process.call_args[0][0]
            self.assertTrue(any('nested/test.py' in f for f in processed_files))

    def test_bydir_output_path_collision(self):
        """Test --bydir handles output path collisions correctly."""
        # Create test directories with same basename
        os.makedirs('src/module', exist_ok=True)
        os.makedirs('other/module', exist_ok=True)
        with open('src/module/test1.py', 'w') as f:
            f.write('def test1():\n    pass\n')
        with open('other/module/test2.py', 'w') as f:
            f.write('def test2():\n    pass\n')
        
        # Create existing output file
        with open('module.tree.md', 'w') as f:
            f.write('existing content')
        
        cli_options = {
            'bydir': True,
            'bydir_dirs': ['src/module', 'other/module'],
            'tree': True,
            'outputFile': True,
            'overwrite': False
        }
        
        with patch('cpai.main.write_output') as mock_write:
            cpai([], cli_options)
            
            # Should not write any files due to collision
            mock_write.assert_not_called()

    def test_nodocs_flag_in_cli_options(self):
        """Test that nodocs flag is properly parsed from CLI arguments."""
        from cpai.cli import parse_arguments, merge_cli_options
        
        # Test without nodocs flag
        args = parse_arguments(['some/path'])
        config = merge_cli_options(args, {})
        assert not config.get('nodocs', False)
        
        # Test with nodocs flag
        args = parse_arguments(['--nodocs', 'some/path'])
        config = merge_cli_options(args, {})
        assert config.get('nodocs', False)

    def test_file_selection_with_nodocs(self):
        """Test that markdown files are properly handled with nodocs flag."""
        from cpai.file_selection import should_process_file
        
        # Create test files
        md_file = os.path.join(self.test_dir, "test.md")
        py_file = os.path.join(self.test_dir, "test.py")
        with open(md_file, 'w') as f:
            f.write('existing content')
        with open(py_file, 'w') as f:
            f.write('def test():\n    pass\n')
        
        # Test without nodocs flag (should include markdown)
        config = {}
        assert should_process_file(md_file, config)
        assert should_process_file(py_file, config)
        
        # Test with nodocs flag (should exclude markdown)
        config = {'nodocs': True}
        assert not should_process_file(md_file, config)
        assert should_process_file(py_file, config)

    def test_get_files_with_nodocs(self):
        """Test that get_files properly handles nodocs flag."""
        from cpai.file_selection import get_files
        
        # Create test directory structure
        test_root = os.path.join(self.test_dir, "nodocs_test")
        docs_dir = os.path.join(test_root, "docs")
        src_dir = os.path.join(test_root, "src")
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(src_dir, exist_ok=True)
        
        # Create test files
        with open(os.path.join(docs_dir, "readme.md"), 'w') as f:
            f.write('# Test readme')
        with open(os.path.join(docs_dir, "api.md"), 'w') as f:
            f.write('# API docs')
        with open(os.path.join(src_dir, "main.py"), 'w') as f:
            f.write('def main():\n    pass\n')
        with open(os.path.join(src_dir, "utils.py"), 'w') as f:
            f.write('def util():\n    pass\n')
        with open(os.path.join(src_dir, "docs.md"), 'w') as f:
            f.write('# Source docs')
        
        # Test without nodocs flag (should include markdown)
        config = {}
        files = get_files(test_root, config)
        assert any(f.endswith('.md') for f in files)
        assert len([f for f in files if f.endswith('.md')]) == 3
        assert len([f for f in files if f.endswith('.py')]) == 2
        
        # Test with nodocs flag (should exclude markdown)
        config = {'nodocs': True}
        files = get_files(test_root, config)
        assert not any(f.endswith('.md') for f in files)
        assert len([f for f in files if f.endswith('.py')]) == 2

if __name__ == '__main__':
    unittest.main()
