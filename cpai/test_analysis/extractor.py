"""Test extraction functionality."""

import ast
import pytest
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from .config import TestAnalysisConfig


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TestLocation:
    """Location information for a test."""
    file_path: Path
    line_number: int
    function_name: str
    class_name: Optional[str] = None


@dataclass
class TestFailure:
    """Information about a failed test."""
    location: TestLocation
    error_message: str
    traceback: str
    test_source: Optional[str] = None


class TestExtractor:
    """Extracts test information from pytest execution."""
    
    def __init__(self, config: TestAnalysisConfig):
        """Initialize the test extractor.
        
        Args:
            config: Configuration for test analysis
        """
        self.config = config
        self._cache: Dict[str, Any] = {}
        
        # Configure logging based on silent flag
        if self.config.silent:
            logging.getLogger(__name__).setLevel(logging.ERROR)
        else:
            logging.getLogger(__name__).setLevel(logging.INFO)
    
    def extract_failing_tests(self, pytest_report: Any) -> List[TestFailure]:
        """Extract information about failing tests from pytest report.
        
        Args:
            pytest_report: The pytest report object containing test results
            
        Returns:
            List of TestFailure objects containing failure information
        """
        failures = []
        for failed in getattr(pytest_report, 'failed', []):
            location = self._extract_test_location(failed)
            if location:
                failure = TestFailure(
                    location=location,
                    error_message=str(failed.longrepr),
                    traceback=self._format_traceback(failed.longrepr),
                    test_source=self.extract_test_function(
                        location.file_path,
                        location.function_name
                    )
                )
                failures.append(failure)
        return failures
    
    def extract_test_function(self, file_path: Path, function_name: str) -> Optional[str]:
        """Extract the source code of a specific test function.
        
        Args:
            file_path: Path to the test file
            function_name: Name of the test function to extract
            
        Returns:
            Source code of the test function if found, None otherwise
        """
        cache_key = f"{file_path}::{function_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef) and 
                    node.name == function_name):
                    # Get the source lines
                    source_lines = []
                    for lineno in range(node.lineno - 1, node.end_lineno):
                        source_lines.append(lineno)
                    
                    with open(file_path, 'r') as f:
                        file_lines = f.readlines()
                        source = ''.join(file_lines[node.lineno - 1:node.end_lineno])
                        self._cache[cache_key] = source
                        return source
                        
        except (IOError, SyntaxError, AttributeError) as e:
            logger.debug(f"Error extracting test function: {e}")
            
        return None
    
    def _extract_test_location(self, test_report: Any) -> Optional[TestLocation]:
        """Extract location information from a test report.
        
        Args:
            test_report: The pytest test report object
            
        Returns:
            TestLocation object if location can be determined, None otherwise
        """
        try:
            nodeid = test_report.nodeid
            # Parse nodeid (format: path/to/test.py::TestClass::test_function)
            parts = nodeid.split("::")
            
            if len(parts) < 2:
                return None
                
            file_path = Path(parts[0])
            
            # Handle both class and function tests
            if len(parts) == 3:
                class_name, function_name = parts[1:]
            else:
                class_name, function_name = None, parts[1]
            
            # Get line number from test report
            location = getattr(test_report, 'location', None)
            line_number = location[1] if location else 1
            
            return TestLocation(
                file_path=file_path,
                line_number=line_number,
                function_name=function_name,
                class_name=class_name
            )
            
        except (AttributeError, IndexError) as e:
            logger.debug(f"Error extracting test location: {e}")
            return None
    
    def _format_traceback(self, longrepr: Any) -> str:
        """Format the traceback from pytest's representation.
        
        Args:
            longrepr: Pytest's long representation of the error
            
        Returns:
            Formatted traceback string
        """
        if hasattr(longrepr, 'reprcrash'):
            return f"{longrepr.reprcrash.path}:{longrepr.reprcrash.lineno}: {longrepr.reprcrash.message}"
        return str(longrepr) 