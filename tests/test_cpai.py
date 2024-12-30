import unittest
import os
import tempfile
import shutil
import json
import argparse
import logging
import subprocess
from unittest.mock import patch, MagicMock
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
from cpai.content_size import tokenize
from cpai.formatter import format_tree
import tiktoken

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

if __name__ == '__main__':
    unittest.main()
