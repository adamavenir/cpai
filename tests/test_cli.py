"""Tests for CLI argument parsing."""
import unittest
from cpai.cli import parse_arguments, merge_cli_options

class TestCLI(unittest.TestCase):
    """Test cases for CLI argument parsing."""
    
    def test_bydir_no_args(self):
        """Test --bydir with no arguments."""
        args = parse_arguments(['--bydir'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['bydir'])
        self.assertEqual(config['bydir_dirs'], ['.'])
        self.assertTrue(config['outputFile'])
        self.assertTrue(config['tree'])

    def test_bydir_with_dirs(self):
        """Test --bydir with specified directories."""
        args = parse_arguments(['--bydir', 'dir1', 'dir2'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['bydir'])
        self.assertEqual(config['bydir_dirs'], ['dir1', 'dir2'])
        self.assertTrue(config['outputFile'])
        self.assertTrue(config['tree'])

    def test_overwrite_option(self):
        """Test --overwrite option."""
        args = parse_arguments(['--overwrite'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['overwrite'])

    def test_overwrite_short_option(self):
        """Test -o short option for overwrite."""
        args = parse_arguments(['-o'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['overwrite'])

    def test_bydir_with_overwrite(self):
        """Test --bydir with --overwrite."""
        args = parse_arguments(['--bydir', 'dir1', '--overwrite'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['bydir'])
        self.assertEqual(config['bydir_dirs'], ['dir1'])
        self.assertTrue(config['overwrite'])
        self.assertTrue(config['outputFile'])
        self.assertTrue(config['tree'])

    def test_tree_preserved_in_bydir(self):
        """Test that --tree is preserved when using --bydir."""
        args = parse_arguments(['--tree', '--bydir'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['tree'])
        self.assertTrue(config['bydir'])

    def test_exclude_with_bydir(self):
        """Test exclude patterns work with --bydir."""
        args = parse_arguments(['--bydir', '--exclude', '*.test.js', 'docs/'])
        config = merge_cli_options(args, {})
        
        self.assertTrue(config['bydir'])
        self.assertEqual(config['exclude'], ['*.test.js', 'docs/'])

if __name__ == '__main__':
    unittest.main() 