"""Test parsing functionality."""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from .config import TestAnalysisConfig


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TestDependency:
    """Information about a test's dependencies."""
    module_name: str
    import_path: str
    is_from_import: bool = False
    imported_names: Optional[List[str]] = None


@dataclass
class TestDefinition:
    """Information about a test function definition."""
    name: str
    line_number: int
    end_line_number: int
    docstring: Optional[str] = None
    fixtures: List[str] = None
    class_name: Optional[str] = None
    is_async: bool = False


class TestParser:
    """Parses test files to extract test information and dependencies."""
    
    def __init__(self, config: TestAnalysisConfig):
        """Initialize the test parser.
        
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
    
    def parse_test_file(self, file_path: Path) -> List[TestDefinition]:
        """Parse a test file to extract test function definitions.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            List of TestDefinition objects
        """
        cache_key = f"test_defs::{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            test_definitions = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    # Handle test methods in classes
                    for method in node.body:
                        if (isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and 
                            method.name.startswith('test_')):
                            test_def = self._extract_test_definition(method, node.name)
                            test_definitions.append(test_def)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Handle standalone test functions
                    if node.name.startswith('test_'):
                        test_def = self._extract_test_definition(node)
                        test_definitions.append(test_def)
            
            self._cache[cache_key] = test_definitions
            return test_definitions
            
        except (IOError, SyntaxError) as e:
            logger.debug(f"Error parsing test file {file_path}: {e}")
            return []
    
    def extract_dependencies(self, file_path: Path) -> List[TestDependency]:
        """Extract import dependencies from a test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            List of TestDependency objects
        """
        cache_key = f"deps::{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            dependencies = []
            seen_imports = set()  # Track unique imports
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name not in seen_imports:
                            seen_imports.add(name.name)
                            dep = TestDependency(
                                module_name=name.name,
                                import_path=name.name,
                                is_from_import=False
                            )
                            dependencies.append(dep)
                elif isinstance(node, ast.ImportFrom):
                    names = [n.name for n in node.names]
                    module_name = node.module or ''
                    if node.level > 0:  # Relative import
                        if not module_name:  # from . import utils
                            module_name = ''
                            import_path = names[0]
                        else:  # from .helpers import helper1, helper2
                            module_name = '.' * node.level + module_name
                            import_path = module_name
                    else:
                        import_path = f"{module_name}.{names[0]}" if module_name else names[0]
                    
                    if import_path not in seen_imports:
                        seen_imports.add(import_path)
                        dep = TestDependency(
                            module_name=module_name,
                            import_path=import_path,
                            is_from_import=True,
                            imported_names=names
                        )
                        dependencies.append(dep)
            
            self._cache[cache_key] = dependencies
            return dependencies
            
        except (IOError, SyntaxError) as e:
            logger.debug(f"Error extracting dependencies from {file_path}: {e}")
            return []
    
    def get_test_fixtures(self, file_path: Path) -> Set[str]:
        """Extract fixture names used in a test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Set of fixture names
        """
        cache_key = f"fixtures::{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        fixtures = set()
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check function arguments for fixtures
                    for arg in node.args.args:
                        if arg.arg != 'self':  # Skip 'self' parameter
                            fixtures.add(arg.arg)
                    
                    # Check for pytest.fixture decorators
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Call) and 
                            isinstance(decorator.func, ast.Name) and
                            decorator.func.id == 'fixture'):
                            fixtures.add(node.name)
                        elif (isinstance(decorator, ast.Attribute) and
                              isinstance(decorator.value, ast.Name) and
                              decorator.value.id == 'pytest' and
                              decorator.attr == 'fixture'):
                            fixtures.add(node.name)
            
            self._cache[cache_key] = fixtures
            return fixtures
            
        except (IOError, SyntaxError) as e:
            logger.debug(f"Error extracting fixtures from {file_path}: {e}")
            return set()
    
    def _extract_test_definition(self, node: ast.AST, class_name: Optional[str] = None) -> TestDefinition:
        """Extract test definition information from an AST node.
        
        Args:
            node: The AST node representing the test function
            class_name: Optional name of the containing class
            
        Returns:
            TestDefinition object
        """
        docstring = ast.get_docstring(node)
        fixtures = [arg.arg for arg in node.args.args if arg.arg != 'self'] if hasattr(node, 'args') else []
        
        return TestDefinition(
            name=node.name,
            line_number=node.lineno,
            end_line_number=node.end_lineno,
            docstring=docstring,
            fixtures=fixtures,
            class_name=class_name,
            is_async=isinstance(node, ast.AsyncFunctionDef)
        ) 