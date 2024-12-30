"""Solidity outline extractor."""
import re
import logging
from typing import List, Optional

from .base import FunctionInfo, OutlineExtractor

class SolidityOutlineExtractor(OutlineExtractor):
    """Extract function information from Solidity files."""
    
    SUPPORTED_EXTENSIONS = {'.sol'}
    
    # Regex patterns for Solidity
    CONTRACT_PATTERN = r'(?:abstract\s+)?contract\s+(\w+)'
    INTERFACE_PATTERN = r'interface\s+(\w+)'
    FUNCTION_PATTERN = r'(?:function|constructor|fallback|receive)\s+(?:(\w+)\s*)?[({]'
    COMMENT_PATTERN = r'(?://[^\n]*|/\*(?:[^*]|\*[^/])*\*/)\s*$'
    
    def supports_file(self, filename: str) -> bool:
        """Check if this extractor supports the given filename."""
        return any(filename.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)
    
    def extract_functions(self, content: str) -> List[FunctionInfo]:
        """Extract function information from Solidity content."""
        functions = []
        current_contract = None
        current_path = []
        seen_names = set()
        
        def get_full_path(name):
            """Get the full path including contract name if inside a contract."""
            path_parts = filter(None, current_path + [name])
            return '.'.join(path_parts)
        
        def should_include_function(name: str) -> bool:
            """Determine if a function should be included in the outline."""
            # Skip internal and private functions
            if name and (name.startswith('_') or name == 'constructor'):
                return False
            return True
        
        try:
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Look for contracts and interfaces
                for pattern in [self.CONTRACT_PATTERN, self.INTERFACE_PATTERN]:
                    match = re.search(pattern, line)
                    if match:
                        name = match.group(1)
                        current_contract = name
                        current_path = [name]
                        break
                
                # Look for functions
                match = re.search(self.FUNCTION_PATTERN, line)
                if match:
                    name = match.group(1) if match.group(1) else 'fallback'
                    if should_include_function(name):
                        full_name = get_full_path(name)
                        if full_name not in seen_names:
                            seen_names.add(full_name)
                            functions.append(FunctionInfo(
                                name=full_name,
                                line_number=i + 1,
                                leading_comment=None
                            ))
        
        except Exception as e:
            logging.error(f"Failed to parse Solidity code: {e}")
        
        return functions
