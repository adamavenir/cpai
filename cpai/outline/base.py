"""Base class for language-specific outline extractors."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class FunctionInfo:
    """Class to store function information."""
    name: str
    line_number: Optional[int] = None
    parameters: Optional[str] = None
    leading_comment: Optional[str] = None
    is_export: bool = False
    is_default_export: bool = False
    node_type: str = 'function'

    @staticmethod
    def is_valid_function_name(name):
        """Check if a function name is valid."""
        if not name:
            return False

        # Skip test functions and setup/teardown methods
        if name.startswith('test_') or name in ('setUp', 'tearDown'):
            return False

        # Skip private methods
        if name.startswith('_'):
            return False

        return True


class OutlineExtractor(ABC):
    """Base class for language-specific outline extractors."""

    @abstractmethod
    def extract_functions(self, content: str) -> List[FunctionInfo]:
        """Extract functions from content."""
        pass

    def format_function_for_clipboard(self, func: FunctionInfo) -> str:
        """Format a single function for clipboard output."""
        return f"{func.name}"

    def format_function_for_tree(self, func: FunctionInfo) -> str:
        """Format a function for tree display.
        
        This can be overridden by language-specific extractors to customize the display.
        """
        if hasattr(func, 'parameters') and func.parameters:
            return f"{func.name}({func.parameters})"
        return f"{func.name}()"

    def format_functions_for_clipboard(self, functions: List[FunctionInfo]) -> str:
        """Format function information for clipboard output."""
        if not functions:
            return ""
        
        # Sort functions by name for consistent ordering
        functions = sorted(functions, key=lambda f: f.name)
        
        # Convert functions to signatures only
        return "\n".join(self.format_function_for_clipboard(func) for func in functions)

    @abstractmethod
    def supports_file(self, filename: str) -> bool:
        """Check if this extractor supports the given filename."""
        pass
