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
    format_tree,
    write_output,
    cpai,
    main,
    configure_logging,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_CHUNK_SIZE
)

class TestCPAI(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directories
        os.makedirs('src/main')
        os.makedirs('src/utils')
        os.makedirs('custom')
        os.makedirs(os.path.join('test_samples', 'python', 'services'))
        
        # Create test files
        with open('src/main/test.py', 'w') as f:
            f.write('def test_func():\n    pass\n')
        with open('src/utils/utils.py', 'w') as f:
            f.write('def util_func():\n    pass\n')
        with open('custom/custom.py', 'w') as f:
            f.write('def custom_func():\n    pass\n')
        with open('custom/test.py', 'w') as f:
            f.write('def test_func():\n    pass\n')
        with open('settings.json', 'w') as f:
            f.write('{"setting": "value"}\n')

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

    def test_read_config_with_invalid_config(self):
        """Test reading invalid configuration file"""
        with open('cpai.config.json', 'w') as f:
            f.write('invalid json')
        
        # Should return default config when JSON is invalid
        config = read_config()
        self.assertIn('include', config)
        self.assertIn('exclude', config)
        self.assertEqual(config['include'], ['.'])  # Check default value

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

    @patch('subprocess.Popen')
    def test_write_output_to_clipboard(self, mock_popen):
        """Test writing output to clipboard"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        config = {
            'outputFile': False,
            'usePastebin': True,
            'chunkSize': 1000,
            'files': ['src/main.py']
        }
        content = "Test content"
        
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
                mock_write.assert_called_once()
        finally:
            # Cleanup
            shutil.rmtree('src')

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

    def test_get_files_with_custom_extensions(self):
        """Test file collection with custom file extensions"""
        config = {
            'include': ['.'],
            'exclude': [],
            'fileExtensions': ['.json']
        }
        files = get_files('.', config, include_all=True)
        self.assertTrue(any('settings.json' in f for f in files))

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

    def test_get_files_with_gitignore(self):
        """Test file collection respecting gitignore patterns"""
        # First, create the gitignore file
        with open('.gitignore', 'w') as f:
            f.write('*.log\n')
            f.write('temp/*\n')  # Changed from temp/ to temp/* to allow negation
            f.write('!temp/keep.txt\n')

        # Create test files that should be ignored
        os.makedirs('temp')
        with open('test.log', 'w') as f:
            f.write('log content')
        with open(os.path.join('temp', 'test.py'), 'w') as f:
            f.write('# test')
        with open(os.path.join('temp', 'keep.txt'), 'w') as f:
            f.write('keep this')

        config = {
            'include': ['.'],
            'exclude': [],
            'fileExtensions': ['.py', '.txt', '.log']
        }
        
        files = get_files('.', config)
        self.assertNotIn('test.log', files)
        self.assertNotIn('temp/test.py', files)
        self.assertIn('temp/keep.txt', files)  # Removed './' prefix

    def test_get_files_with_config_patterns(self):
        """Test file collection with config patterns"""
        # Create config files
        try:
            with open('package.json', 'w') as f:
                f.write('{}')
            with open('tsconfig.json', 'w') as f:
                f.write('{}')
            with open('settings.json', 'w') as f:
                f.write('{}')

            config = {
                'include': ['.'],
                'exclude': [],  # Explicitly disable default excludes
                'fileExtensions': ['.json']  # Only look for JSON files
            }

            files = get_files('.', config)
            json_files = [f for f in files if f.endswith('.json')]
            self.assertTrue(len(json_files) >= 3)  # Should find at least our 3 JSON files
        finally:
            # Cleanup
            for f in ['package.json', 'tsconfig.json', 'settings.json']:
                if os.path.exists(f):
                    os.remove(f)

    def test_format_tree_empty(self):
        """Test tree formatting with empty input"""
        self.assertEqual(format_tree([]), '')

    def test_format_tree_nested(self):
        """Test tree formatting with deeply nested structure"""
        files = [
            'src/components/ui/button.js',
            'src/components/ui/input.js',
            'src/components/layout/header.js',
            'src/utils/format.js'
        ]
        tree = format_tree(files)
        self.assertIn('src', tree)
        self.assertIn('components', tree)
        self.assertIn('ui', tree)
        self.assertIn('layout', tree)
        self.assertIn('utils', tree)
        self.assertIn('button.js', tree)

    @patch('sys.argv')
    def test_main_with_all_options(self, mock_argv):
        """Test main function with various CLI options"""
        test_args = [
            'cpai',
            'src/',
            '-f', 'output.md',
            '--debug',
            '-a',
            '-x', 'tests/', 'docs/'
        ]
        mock_argv.__getitem__.side_effect = lambda i: test_args[i]
        mock_argv.__len__.return_value = len(test_args)

        with patch('cpai.main.cpai') as mock_cpai:
            main()
            mock_cpai.assert_called_once()
            cli_options = mock_cpai.call_args[0][1]
            self.assertEqual(cli_options['outputFile'], 'output.md')
            self.assertTrue(cli_options['include_all'])
            self.assertEqual(cli_options['exclude'], ['tests/', 'docs/'])

    def test_write_output_large_content(self):
        """Test write_output with content exceeding chunk size"""
        config = {
            'outputFile': 'large_output.md',
            'usePastebin': True,
            'chunkSize': 10,  # Small chunk size for testing
            'files': ['src/main.py', 'src/utils.py']
        }
        content = "This is a test content"  # 22 characters (including spaces)
        
        with patch('builtins.print') as mock_print:
            write_output(content, config)
            mock_print.assert_any_call("\nWarning: Content size (22 characters) exceeds the maximum size (10 characters).")

    def test_get_files_with_custom_include(self):
        """Test file collection with custom include patterns"""
        config = {
            'include': ['custom/**/*.py'],
            'exclude': [],
            'fileExtensions': ['.py']
        }

        files = get_files('.', config)
        self.assertTrue(any('custom/custom.py' in f for f in files))

    @patch('logging.warning')
    def test_cpai_no_files_found(self, mock_warning):
        """Test cpai function when no files are found"""
        cli_options = {
            'outputFile': False,
            'usePastebin': False,
            'include_all': False,
            'fileExtensions': ['.xyz']  # Use a non-existent extension
        }
        
        cpai([], cli_options)
        mock_warning.assert_called_with("No files found to process")

    def test_read_config_with_invalid_fields(self):
        """Test reading config with various invalid fields"""
        config_data = {
            "include": "not_a_list",  # Should be a list
            "exclude": {"invalid": "type"},  # Should be a list
            "chunkSize": "not_an_int",  # Should be an integer
            "outputFile": []  # Should be bool or string
        }
        with open('cpai.config.json', 'w') as f:
            json.dump(config_data, f)
        
        config = read_config()
        self.assertEqual(config['include'], ['.'])  # Should use default
        self.assertEqual(config['exclude'], DEFAULT_EXCLUDE_PATTERNS)  # Should use default
        self.assertEqual(config['chunkSize'], DEFAULT_CHUNK_SIZE)  # Should use default
        self.assertFalse(config['outputFile'])  # Should use default

    def test_main_module_execution(self):
        """Test direct module execution through __main__.py"""
        with patch('sys.argv', ['cpai']):
            with patch('cpai.main.main') as mock_main:
                # Import and execute __main__.py directly
                import runpy
                runpy.run_module('cpai.__main__', run_name='__main__', alter_sys=True)
                mock_main.assert_called_once()

    def test_clipboard_error_handling(self):
        """Test clipboard operations with errors"""
        config = {
            'outputFile': False,
            'usePastebin': True,
            'chunkSize': 1000,
            'files': ['test.py']
        }
        content = "Test content"
        
        # Test subprocess error
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: Command returned non-zero exit status 1"
                )

        # Test encoding error
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = UnicodeEncodeError('utf-8', 'test', 0, 1, 'test error')
            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: 'utf-8' codec can't encode character '\\x74' in position 0: test error"
                )

    def test_main_module_direct_execution(self):
        """Test direct execution through __main__.py"""
        with patch('sys.argv', ['cpai']):
            with patch('cpai.main.main') as mock_main:
                # Import and execute __main__.py
                import runpy
                runpy.run_module('cpai.__main__', run_name='__main__')
                mock_main.assert_called_once()

    def test_format_tree_with_empty_subtree(self):
        """Test tree formatting with empty subtree"""
        files = [
            'src/empty/',
            'src/file.py'
        ]
        tree = format_tree(files)
        self.assertIn('src', tree)
        self.assertIn('empty', tree)
        self.assertIn('file.py', tree)

    def test_get_files_with_broken_symlinks(self):
        """Test file collection with broken symlinks"""
        # Create a broken symlink
        os.symlink('nonexistent.py', 'broken_link.py')
        
        config = {
            'include': ['.'],
            'exclude': [],
            'fileExtensions': ['.py']
        }
        
        try:
            files = get_files('.', config)
            self.assertNotIn('broken_link.py', files)
        finally:
            os.unlink('broken_link.py')

    def test_write_output_with_unicode_error(self):
        """Test clipboard operations with Unicode errors"""
        config = {
            'outputFile': False,
            'usePastebin': True,
            'chunkSize': 1000,
            'files': ['test.py']
        }

        # Create content with problematic Unicode
        content = "Test content with unicode \udcff"

        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = UnicodeEncodeError(
                'utf-8', content, 26, 27, 'surrogates not allowed'
            )
            mock_popen.return_value = mock_process

            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: 'utf-8' codec can't encode character '\\udcff' in position 26: surrogates not allowed"
                )

    def test_format_tree_with_special_characters(self):
        """Test tree formatting with special characters in paths"""
        files = [
            'src/special!@#$/file.py',
            'src/unicode⚡/test.py'
        ]
        tree = format_tree(files)
        self.assertIn('special!@#$', tree)
        self.assertIn('unicode⚡', tree)

    def test_main_with_keyboard_interrupt(self):
        """Test main function handling KeyboardInterrupt"""
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.file = None
        mock_args.noclipboard = False
        mock_args.all = False
        mock_args.configs = False
        mock_args.exclude = None
        mock_args.files = []

        with patch('argparse.ArgumentParser.parse_args', return_value=mock_args):
            with patch('cpai.main.cpai', side_effect=KeyboardInterrupt):
                with patch('sys.exit') as mock_exit:
                    with patch('logging.error') as mock_error:
                        main()
                        mock_exit.assert_called_once_with(1)
                        mock_error.assert_called_once()

    def test_get_files_with_permission_error(self):
        """Test file collection with permission errors"""
        # Create a directory with no read permissions
        os.makedirs('no_access')
        os.chmod('no_access', 0o000)
        
        config = {
            'include': ['.'],
            'exclude': [],
            'fileExtensions': ['.py']
        }
        
        try:
            files = get_files('.', config)
            self.assertNotIn('no_access/test.py', files)
        finally:
            os.rmdir('no_access')

    def test_write_output_clipboard_errors(self):
        """Test clipboard operations with various errors"""
        config = {
            'outputFile': False,
            'usePastebin': True,
            'chunkSize': 1000,
            'files': ['test.py']
        }
        content = "Test content"

        # Test non-zero return code
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: Command returned non-zero exit status 1"
                )

        # Test subprocess error
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = subprocess.CalledProcessError(1, 'pbcopy')
            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: Command 'pbcopy' returned non-zero exit status 1"
                )

        # Test encoding error
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = UnicodeEncodeError('utf-8', 'test', 0, 1, 'test error')
            with patch('logging.error') as mock_error:
                write_output(content, config)
                mock_error.assert_called_with(
                    "Failed to copy to clipboard: 'utf-8' codec can't encode character '\\x74' in position 0: test error"
                )

    def test_get_files_with_none_exclude(self):
        """Test file collection with None exclude patterns"""
        config = {
            'include': ['.'],
            'exclude': None,  # This should not cause an error
            'fileExtensions': ['.py']
        }

        # This should not raise a TypeError
        files = get_files('.', config)
        self.assertIsInstance(files, list)

    def test_dirs_only_mode(self):
        """Test directory-only mode."""
        # Create test directories and files
        os.makedirs('src/components', exist_ok=True)
        os.makedirs('src/utils', exist_ok=True)
        os.makedirs('test', exist_ok=True)
        with open('src/components/test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        
        config = {
            'dirs_only': True,
            'include': ['.']
        }
        
        files = get_files('src', config)
        rel_files = [os.path.basename(f) for f in files]
        
        # Should only include directories, not files
        self.assertEqual(set(rel_files), {'components', 'utils'})
        
    def test_nodocs_mode(self):
        """Test exclusion of documentation files."""
        # Create test files
        with open('test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        with open('README.md', 'w') as f:
            f.write('# Test\n')
        with open('docs.txt', 'w') as f:
            f.write('Documentation\n')
        
        config = {
            'nodocs': True,
            'include': ['.']
        }
        
        files = get_files('.', config)
        rel_files = [os.path.basename(f) for f in files]
        
        # Should exclude .md and .txt files
        self.assertNotIn('README.md', rel_files)
        self.assertNotIn('docs.txt', rel_files)
        self.assertIn('test.py', rel_files)
        
    def test_directory_variable_filename(self):
        """Test directory variable in output filename."""
        # Create test directory
        os.makedirs('src/components', exist_ok=True)
        
        config = {
            'dirs_only': True,
            'outputFile': '{dir}.tree.md',
            'files': [os.path.abspath('src/components')]
        }
        
        # Write some test content
        content = "Test content"
        write_output(content, config)
        
        # Check if the file was created with the correct name
        expected_filename = 'components.tree.md'
        self.assertTrue(os.path.exists(expected_filename))
        
        # Clean up
        os.remove(expected_filename)
        
    def test_combined_features(self):
        """Test combination of directory-only mode, nodocs, and tree output."""
        # Create test structure
        os.makedirs('src/components', exist_ok=True)
        os.makedirs('src/utils', exist_ok=True)
        os.makedirs('docs', exist_ok=True)
        with open('src/components/test.py', 'w') as f:
            f.write('def test():\n    pass\n')
        with open('src/README.md', 'w') as f:
            f.write('# Test\n')
        
        config = {
            'dirs_only': True,
            'nodocs': True,
            'tree': True,
            'include': ['.']
        }
        
        files = get_files('src', config)
        rel_files = [os.path.basename(f) for f in files]
        
        # Should only include directories and exclude docs
        self.assertEqual(set(rel_files), {'components', 'utils'})
        self.assertTrue(all(os.path.isdir(f) for f in files))
        
        # Test tree output
        tree = format_tree(files)
        self.assertIn('components', tree)
        self.assertIn('utils', tree)
        self.assertNotIn('README.md', tree)
        
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up additional test directories
        for dir_name in ['src', 'test', 'docs']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
        # Clean up test files
        for file_name in ['test.py', 'README.md', 'docs.txt']:
            if os.path.exists(file_name):
                os.remove(file_name)

    def test_directory_specific_output_files(self):
        """Test that separate output files are created for each directory when using {dir} template."""
        # Create test directories and files
        os.makedirs('src/components', exist_ok=True)
        os.makedirs('src/utils', exist_ok=True)
        os.makedirs('lib/core', exist_ok=True)
        
        with open('src/components/Button.js', 'w') as f:
            f.write('export function Button() { return null; }')
        with open('src/utils/format.js', 'w') as f:
            f.write('export function format() { return ""; }')
        with open('lib/core/main.js', 'w') as f:
            f.write('export function main() { return 0; }')
        
        try:
            cli_options = {
                'dirs_only': True,
                'outputFile': '{dir}.tree.md',
                'tree': True,
                'include': ['.'],
                'fileExtensions': ['.js']
            }
            
            # Process directories
            cpai(['src', 'lib'], cli_options)
            
            # Verify output files were created
            self.assertTrue(os.path.exists('src.tree.md'))
            self.assertTrue(os.path.exists('lib.tree.md'))
            
            # Verify content - in dirs_only mode, we only show directories
            with open('src.tree.md', 'r') as f:
                src_content = f.read()
                self.assertIn('components', src_content)
                self.assertIn('utils', src_content)
                self.assertNotIn('core', src_content)
            
            with open('lib.tree.md', 'r') as f:
                lib_content = f.read()
                self.assertIn('core', lib_content)
                self.assertNotIn('components', lib_content)
                self.assertNotIn('utils', lib_content)
        finally:
            # Clean up
            for file in ['src.tree.md', 'lib.tree.md']:
                if os.path.exists(file):
                    os.remove(file)
            shutil.rmtree('src')
            shutil.rmtree('lib')

    def test_tree_structure_formatting(self):
        """Test that the tree structure is properly formatted in dirs_only mode."""
        # Create test directories
        os.makedirs('src/components/ui', exist_ok=True)
        os.makedirs('src/utils/format', exist_ok=True)
        os.makedirs('lib/core/utils', exist_ok=True)
        
        try:
            cli_options = {
                'dirs_only': True,
                'tree': True,
                'include': ['.']
            }
            
            # Process directories
            result = cpai(['src', 'lib'], cli_options)
            
            # Verify tree structure formatting
            self.assertIn('```', result)
            self.assertIn('    .', result)
            self.assertIn('    ├── lib', result)
            self.assertIn('    │   └── core', result)
            self.assertIn('    │       └── utils', result)
            self.assertIn('    └── src', result)
            self.assertIn('        ├── components', result)
            self.assertIn('        │   └── ui', result)
            self.assertIn('        └── utils', result)
            self.assertIn('            └── format', result)
            
        finally:
            # Clean up
            shutil.rmtree('src')
            shutil.rmtree('lib')

    def test_none_value_handling(self):
        """Test that None values are handled gracefully when processing files."""
        # Create test directory structure
        os.makedirs('src', exist_ok=True)
        os.makedirs('docs', exist_ok=True)
        
        try:
            # Create test files
            with open('src/test.py', 'w') as f:
                f.write('def test():\n    pass\n')
            with open('docs/README.md', 'w') as f:
                f.write('# Test\n')
            
            cli_options = {
                'outputFile': False,
                'usePastebin': False,
                'dirs_only': True,  # This should trigger directory processing
                'nodocs': True,     # This should exclude docs
                'tree': True        # This should trigger tree view
            }
            
            # Process files - this should not raise any NoneType errors
            result = cpai(['.'], cli_options)
            
            # Verify we got a result
            self.assertIsNotNone(result)
            
            # Verify docs directory was excluded
            self.assertNotIn('docs', result)
            
            # Verify src directory was included
            self.assertIn('src', result)
            
        finally:
            # Clean up
            shutil.rmtree('src')
            shutil.rmtree('docs')

if __name__ == '__main__':
    unittest.main()
