"""Test exclude pattern handling."""
import unittest
import os
import tempfile
import shutil
from cpai.file_selection import should_process_file
from cpai.constants import DEFAULT_EXCLUDE_PATTERNS

class TestExcludePatterns(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test files and directories
        os.makedirs('src')
        os.makedirs('lib')
        
        with open('src/main.py', 'w') as f:
            f.write('print("Hello")\n')
        with open('src/utils.js', 'w') as f:
            f.write('console.log("Hello")\n')
        with open('lib/helpers.ts', 'w') as f:
            f.write('export const helper = () => {}\n')
        with open('README.md', 'w') as f:
            f.write('# Test Project\n')

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_default_exclude_patterns(self):
        """Test that default exclude patterns work correctly."""
        test_files = {
            'src/main.py',
            'src/utils.js',
            'lib/helpers.ts',
            'README.md'
        }
        
        # Test each file against default exclude patterns
        config = {'exclude': DEFAULT_EXCLUDE_PATTERNS}
        included_files = {f for f in test_files if should_process_file(f, config)}
        
        # All test files should be included (not excluded by default patterns)
        self.assertEqual(included_files, test_files)
