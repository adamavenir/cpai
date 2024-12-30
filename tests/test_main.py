import unittest
import os
import tempfile
import shutil
from cpai.file_selection import get_files

class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test files and directories
        os.makedirs('src')
        os.makedirs('lib')
        os.makedirs('test')
        
        with open('src/main.py', 'w') as f:
            f.write('print("Hello")\n')
        with open('src/utils.js', 'w') as f:
            f.write('console.log("Hello")\n')
        with open('lib/helpers.ts', 'w') as f:
            f.write('export const helper = () => {}\n')
        with open('test/test_main.py', 'w') as f:
            f.write('def test_main():\n    pass\n')
            
        # Create symlinks for testing
        if os.name != 'nt':  # Skip on Windows
            os.symlink('../src/main.py', 'src/main_link.py')
            os.symlink('nonexistent.py', 'src/broken_link.py')

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_get_files_basic(self):
        """Test basic file collection."""
        expected_files = {
            'src/main.py',
            'src/utils.js',
            'lib/helpers.ts',
            'test/test_main.py',
            'src/main_link.py'
        }
        
        config = {'include': ['**/*']}  # Include all files
        files = set(os.path.normpath(f) for f in get_files('.', config))
        
        # Convert expected files to use OS-specific path separators
        expected = set(os.path.normpath(f) for f in expected_files)
        
        self.assertEqual(files, expected)

    def test_get_files_symlinks(self):
        """Test file collection with symlinks."""
        if os.name == 'nt':  # Skip on Windows
            self.skipTest("Symlink tests not supported on Windows")
            
        config = {'include': ['**/*']}  # Include all files
        files = set(os.path.normpath(f) for f in get_files('.', config))
        
        # Check that symlinks are followed
        self.assertIn(os.path.normpath('src/main_link.py'), files)
        # Check that broken symlinks are ignored
        self.assertNotIn(os.path.normpath('src/broken_link.py'), files)
