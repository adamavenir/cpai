import os
import sys
import json
import argparse
import subprocess
import textwrap
import logging
import fnmatch
import tempfile
import re
from typing import List, Dict, Any, Optional
from .outline.base import FunctionInfo, OutlineExtractor
from .outline import EXTRACTORS
import pathspec
from .constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EXCLUDE_PATTERNS,
    CORE_SOURCE_PATTERNS,
    DEFAULT_FILE_EXTENSIONS,
    CLIPBOARD_ICON,
    FILE_ICON,
    STDOUT_ICON
)
from .file_selection import get_files, should_process_file, get_relative_path, should_match_pattern
from .content_size import validate_content_size
from .formatter import (
    format_functions_as_tree,
    format_outline_tree,
    build_tree_structure,
    format_tree_with_outlines,
    format_content,
    get_language_from_ext,
    get_extractor_for_ext
)
from .cli import parse_arguments, merge_cli_options
from .config import configure_logging, read_config
from .progress import ProgressIndicator

def write_output(content, config):
    """Write content to file, clipboard, or stdout."""
    # Validate content size
    size_info = validate_content_size(content, config.get('chunkSize', DEFAULT_CHUNK_SIZE))
    
    # Print to stdout if specified - only output content, no metadata
    if config.get('stdout', False):
        sys.stdout.write(content)
        return
    
    # Write to file if specified
    if config.get('outputFile'):
        output_file = config['outputFile']
        if isinstance(output_file, bool):
            output_file = 'cpai_output.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        # Get relative path for display
        rel_path = os.path.relpath(output_file)
        # Show metadata on stderr
        compat_text = size_info['compatibility']
        compat_text = compat_text.replace("Output content compatibility:\n", "").strip()
        sys.stderr.write("\nInput limits: " + compat_text + "\n")
        sys.stderr.write(f"{FILE_ICON} {size_info['formatted_chars']} characters ({size_info['formatted_tokens']} tokens) written to {rel_path}\n")
        return
    
    # Otherwise copy to clipboard and show metadata on stderr
    try:
        # Create a temporary file for the content
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as temp_file:
            temp_file.write(content)
            temp_file.flush()
            
            # Use pbcopy on macOS
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(content.encode('utf-8'))
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, 'pbcopy')
                
        # Show metadata on stderr
        compat_text = size_info['compatibility']
        compat_text = compat_text.replace("Output content compatibility:\n", "").strip()
        sys.stderr.write("\nInput limits: " + compat_text + "\n")
        
        # Show clipboard message
        if config.get('tree'):
            sys.stderr.write(f"📋 {size_info['formatted_chars']} characters ({size_info['formatted_tokens']} tokens) - tree copied to clipboard!\n")
        else:
            sys.stderr.write(f"📋 {size_info['formatted_chars']} characters ({size_info['formatted_tokens']} tokens) copied to clipboard\n")
            
    except (subprocess.CalledProcessError, UnicodeEncodeError) as e:
        logging.error(f"Failed to copy to clipboard: {str(e)}")

def process_files(files: List[str], config: Dict = None) -> Dict[str, Dict]:
    """Process multiple files and return their content."""
    if config is None:
        config = {}
        
    # Initialize result dictionary
    result = {}
    
    # Process each file
    for file_path in files:
        if should_process_file(file_path, config):
            file_data = process_file(file_path, config)
            if file_data:  # Only include successfully processed files
                # Get the basename for the key
                rel_path = os.path.basename(file_path)
                result[rel_path] = file_data
                
    return result

def process_file(file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single file and return its content and outline."""
    try:
        # In tree mode, we only need the outline
        if options.get('tree'):
            outline = extract_outline(file_path)
            # Return empty outline instead of None if extraction fails
            return {'outline': outline or []}
            
        # For regular mode, get both content and outline
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        outline = extract_outline(file_path)
        return {
            'content': content,
            'outline': outline or []  # Return empty list instead of None
        }
        
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return {'outline': []} if options.get('tree') else None  # Return empty outline in tree mode

def extract_outline(file_path):
    """Extract function outlines from a file."""
    from .outline import EXTRACTORS
    
    try:
        # Find the appropriate extractor
        for extractor in EXTRACTORS:
            if extractor.supports_file(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return extractor.extract_functions(content)
        return []
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return None

def cpai(args, cli_options):
    """Main function for the cpai tool."""
    # Configure logging
    configure_logging(cli_options.get('debug', False))
    
    # Read config and merge with CLI options
    config = read_config()
    config.update(cli_options)
    
    if config.get('bydir'):
        # Process each directory independently
        base_dirs = config['bydir_dirs']
        processed_dirs = set()  # Track processed directories
        
        # If using current directory, get immediate subdirectories
        if base_dirs == ['.']:
            base_dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
        
        # Store current directory
        original_cwd = os.getcwd()
        
        for dir_path in base_dirs:
            # Skip if already processed
            if dir_path in processed_dirs:
                continue
            processed_dirs.add(dir_path)
            
            # Get absolute path
            abs_dir_path = os.path.abspath(dir_path)
            
            # Change to directory before processing
            try:
                os.chdir(original_cwd)  # Always start from original directory
                os.chdir(abs_dir_path)
                
                # Get files for this directory
                dir_files = []
                dir_files.extend(get_files('.', config))
                
                if not dir_files:
                    logging.warning(f"No files found to process in {dir_path}")
                    continue
                    
                # Create a copy of config for this directory
                dir_config = config.copy()
                dir_config['files'] = dir_files
                
                # Set output file name based on directory name
                dir_name = os.path.basename(abs_dir_path)
                output_file = os.path.join(original_cwd, f"{dir_name}.tree.md")
                
                # Check if output file exists and we don't have overwrite permission
                if os.path.exists(output_file) and not config.get('overwrite'):
                    if not config.get('confirmed_overwrite'):
                        print(f"Output file {output_file} already exists. Use --overwrite to force overwrite.")
                        continue
                
                dir_config['outputFile'] = output_file
                
                # Show progress indicator
                progress = ProgressIndicator(f"Processing {dir_name}")
                progress.start()
                
                try:
                    # Process files in this directory
                    processed_files = process_files(dir_files, dir_config)
                    
                    # Format content
                    content = format_content(processed_files, dir_config)
                    
                    # Write output
                    write_output(content, dir_config)
                finally:
                    progress.stop()
            except Exception as e:
                logging.error(f"Error processing directory {dir_path}: {str(e)}")
            finally:
                # Always restore original directory
                os.chdir(original_cwd)
            
        return None  # No single content to return in bydir mode
    else:
        # Original single-output mode
        files = []
        # If no paths provided, use current directory
        paths = args if args else ['.']
        for path in paths:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                files.extend(get_files(abs_path, config))
            else:
                files.append(abs_path)
                
        if not files:
            logging.warning("No files found to process.")
            return None
            
        # Add files to config for reference
        config['files'] = files
        
        # Show progress indicator
        progress = ProgressIndicator("Processing")
        progress.start()
        
        try:
            # Process files
            processed_files = process_files(files, config)
            
            # Format content
            content = format_content(processed_files, config)
            
            # Write output
            write_output(content, config)
            
            return content
        finally:
            progress.stop()

def main():
    """Entry point for the cpai tool."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure logging
    configure_logging(args.debug)
    
    # Read config and merge with CLI options
    config = read_config()
    config = merge_cli_options(args, config)
    
    # Call main function
    cpai(args.files, config)

if __name__ == '__main__':
    main()