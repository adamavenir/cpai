"""Test exclude pattern handling."""
import os
import tempfile
import shutil
from cpai.main import get_files
from cpai.constants import DEFAULT_EXCLUDE_PATTERNS

def test_default_exclude_patterns():
    """Test that default exclude patterns work correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files and directories
        test_files = [
            # Should be excluded (build/cache)
            'build/output.js',
            'dist/bundle.js',
            '__pycache__/module.pyc',
            '.cache/data.bin',
            
            # Should be excluded (dependencies)
            'node_modules/package/index.js',
            'venv/lib/python3.8/site-packages/module.py',
            
            # Should be excluded (tests)
            'test/test_file.py',
            'tests/unit/test_module.py',
            'src/module.test.js',
            'lib/module.spec.ts',
            
            # Should be excluded (IDE/OS)
            '.idea/workspace.xml',
            '.vscode/settings.json',
            '.DS_Store',
            
            # Should be excluded (VCS)
            '.git/HEAD',
            
            # Should be excluded (logs/temp)
            'error.log',
            'debug.log',
            
            # Should be excluded (dotfiles)
            '.env',
            '.envrc',
            '.env.local',
            '.python-version',
            
            # Should be included
            'src/main.py',
            'src/utils.js',
            'lib/helpers.ts',
            'README.md'
        ]
        
        # Create all test files
        for file_path in test_files:
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write('test content')
        
        # Get files using default config
        config = {
            'exclude': DEFAULT_EXCLUDE_PATTERNS.copy(),
            'include': ['.'],
            'fileExtensions': ['.py', '.js', '.ts', '.md']
        }
        
        # Get files and convert to relative paths
        files = get_files(temp_dir, config)
        rel_files = {os.path.relpath(f, temp_dir) for f in files}
        
        # These files should be included
        should_include = {
            'src/main.py',
            'src/utils.js',
            'lib/helpers.ts',
            'README.md'
        }
        
        # These files represent each exclude category and should be excluded
        should_exclude = {
            'build/output.js',          # Build/cache
            'node_modules/package/index.js',  # Dependencies
            'tests/unit/test_module.py',  # Tests
            '.vscode/settings.json',    # IDE
            '.git/HEAD',               # VCS
            'error.log',               # Logs
            '.env'                     # Dotfiles
        }
        
        # Verify included files
        assert rel_files == should_include, f"Expected {should_include}, but got {rel_files}"
        
        # Verify excluded files
        for excluded in should_exclude:
            excluded_path = os.path.join(temp_dir, excluded)
            assert excluded_path not in files, f"File should be excluded: {excluded}"
