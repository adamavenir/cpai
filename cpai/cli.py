"""Module for handling command-line arguments and user-facing main invocation."""
import argparse
import sys
from typing import List, Dict, Any, Optional

def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        argv: List of command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate a tree view of files and their functions.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        default=['.'],
        help='Files or directories to process'
    )
    
    parser.add_argument(
        '-f', '--file',
        help='Write output to file instead of clipboard'
    )
    
    parser.add_argument(
        '--stdout',
        action='store_true',
        help='Print output to stdout instead of clipboard'
    )
    
    parser.add_argument(
        '--noclipboard',
        action='store_true',
        help='Disable clipboard output'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Include all files (ignore .gitignore)'
    )
    
    parser.add_argument(
        '--nodocs',
        action='store_true',
        help='Exclude documentation files (.md)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Additional patterns to exclude'
    )
    
    parser.add_argument(
        '--tree',
        action='store_true',
        help='Generate a tree view of files and functions'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--bydir',
        nargs='*',
        help='Process directories independently and output to {dir}.tree.md files. If no directories are specified, processes all non-excluded directories in current path.'
    )
    
    parser.add_argument(
        '--overwrite', '-o',
        action='store_true',
        help='Overwrite existing output files without confirmation'
    )
    
    return parser.parse_args(argv)

def merge_cli_options(args: argparse.Namespace, config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge command-line arguments into configuration.
    
    Args:
        args: Parsed command-line arguments
        config: Configuration dictionary
        
    Returns:
        Updated configuration dictionary
    """
    # Handle bydir mode
    if args.bydir is not None:
        config['bydir'] = True
        config['bydir_dirs'] = args.bydir if args.bydir else ['.']
        # In bydir mode, we always output to files named {dir}.tree.md
        config['outputFile'] = True
        config['tree'] = True  # Force tree mode in bydir mode
    else:
        config['bydir'] = False
        config['bydir_dirs'] = []
        config.update({
            'outputFile': args.file if args.file is not None else False,
            'usePastebin': not args.noclipboard and not args.stdout,
            'stdout': args.stdout
        })

    # Common options that apply in both modes
    config.update({
        'include_all': args.all,
        'tree': args.tree or config.get('tree', False),  # Keep tree mode if set by bydir
        'overwrite': args.overwrite,  # Add overwrite option
        'nodocs': args.nodocs  # Add nodocs option
    })
    
    # Add exclude patterns if specified
    if args.exclude:
        if 'exclude' not in config:
            config['exclude'] = []
        config['exclude'].extend(args.exclude)
        
    return config 