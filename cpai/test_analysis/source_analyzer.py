"""Source code analysis functionality."""

import ast
import logging
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from .config import TestAnalysisConfig


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class SourceLocation:
    """Information about a source code location."""
    file_path: Path
    line_number: int
    end_line_number: int
    module_name: str


@dataclass
class SourceContext:
    """Context information about source code."""
    location: SourceLocation
    source_code: str
    imports: List[str]
    dependencies: Set[str]


class SourceAnalyzer:
    """Analyzes source code files and their dependencies."""
    
    def __init__(self, config: TestAnalysisConfig):
        """Initialize the source analyzer.
        
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
    
    def find_source_file(self, module_name: str) -> Optional[Path]:
        """Find the source file for a given module.
        
        Args:
            module_name: Name of the module to find
            
        Returns:
            Path to the source file if found, None otherwise
        """
        logger.debug(f"Looking for module: {module_name}")
        logger.debug(f"Workspace dir: {self.config.workspace_dir}")
        
        cache_key = f"source_file::{module_name}"
        if cache_key in self._cache:
            logger.debug(f"Using cached result for {module_name}")
            return self._cache[cache_key]
        
        # Try to find the module spec first
        logger.debug(f"Trying to find module spec for {module_name}")
        try:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                source_path = Path(spec.origin)
                if source_path.suffix == '.py':
                    logger.debug(f"Found module through importlib: {source_path}")
                    self._cache[cache_key] = source_path
                    return source_path
        except (ImportError, ValueError) as e:
            logger.debug(f"Error finding module spec for {module_name}: {e}")
            # Continue to try workspace paths
        
        # If not found through importlib, try relative to workspace
        if self.config.workspace_dir:
            workspace = Path(self.config.workspace_dir)
            module_parts = module_name.split('.')
            logger.debug(f"Looking for module {module_name} in workspace {workspace}")
            logger.debug(f"Module parts: {module_parts}")
            
            # For a single module name, try as a package first
            if len(module_parts) == 1:
                init_path = workspace / module_parts[0] / "__init__.py"
                logger.debug(f"Trying package init path: {init_path}")
                if init_path.exists():
                    logger.debug(f"Found package init file: {init_path}")
                    self._cache[cache_key] = init_path
                    return init_path
                module_path = workspace / f"{module_parts[0]}.py"
                logger.debug(f"Trying module path: {module_path}")
                if module_path.exists():
                    logger.debug(f"Found module file: {module_path}")
                    self._cache[cache_key] = module_path
                    return module_path
            
            # For submodules, try all possible locations
            else:
                # Try as a module file in parent package (e.g., mymodule/source.py)
                parent_path = workspace.joinpath(*module_parts[:-1])
                logger.debug(f"Parent path: {parent_path}")
                if parent_path.exists() and parent_path.is_dir():
                    module_path = parent_path / f"{module_parts[-1]}.py"
                    logger.debug(f"Trying module path: {module_path}")
                    if module_path.exists():
                        logger.debug(f"Found module file: {module_path}")
                        self._cache[cache_key] = module_path
                        return module_path
                    
                    # Try as a package (e.g., mymodule/source/__init__.py)
                    init_path = module_path.parent / module_parts[-1] / "__init__.py"
                    logger.debug(f"Trying init path: {init_path}")
                    if init_path.exists():
                        logger.debug(f"Found package init file: {init_path}")
                        self._cache[cache_key] = init_path
                        return init_path
                
                # Try as a direct module file (e.g., mymodule/source.py)
                direct_path = workspace / f"{module_name.replace('.', '/')}.py"
                logger.debug(f"Trying direct path: {direct_path}")
                if direct_path.exists():
                    logger.debug(f"Found direct module file: {direct_path}")
                    self._cache[cache_key] = direct_path
                    return direct_path
                
                logger.debug("No matching module file found")
        
        return None
    
    def extract_imports(self, file_path: Path) -> List[str]:
        """Extract import statements from a source file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of imported module names
        """
        cache_key = f"imports::{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0:  # Only include absolute imports
                        if node.module:
                            imports.add(node.module)
            
            result = sorted(list(imports))
            self._cache[cache_key] = result
            return result
            
        except (IOError, SyntaxError) as e:
            logger.debug(f"Error extracting imports from {file_path}: {e}")
            return []
    
    def analyze_dependencies(self, file_path: Path, max_depth: int = 3) -> Set[str]:
        """Analyze dependencies of a source file recursively.
        
        Args:
            file_path: Path to the source file
            max_depth: Maximum recursion depth for dependency analysis
            
        Returns:
            Set of all dependent module names
        """
        cache_key = f"deps::{file_path}::{max_depth}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if max_depth <= 0:
            return set()
        
        try:
            direct_imports = set(self.extract_imports(file_path))
            all_deps = direct_imports.copy()
            
            for module_name in direct_imports:
                dep_file = self.find_source_file(module_name)
                if dep_file:
                    nested_deps = self.analyze_dependencies(dep_file, max_depth - 1)
                    all_deps.update(nested_deps)
            
            self._cache[cache_key] = all_deps
            return all_deps
            
        except Exception as e:
            logger.debug(f"Error analyzing dependencies for {file_path}: {e}")
            return set()
    
    def get_source_context(self, file_path: Path, line_number: int, context_lines: int = 5) -> Optional[SourceContext]:
        """Get source code context around a specific line.
        
        Args:
            file_path: Path to the source file
            line_number: Line number to get context around
            context_lines: Number of lines of context before and after
            
        Returns:
            SourceContext object if successful, None otherwise
        """
        cache_key = f"context::{file_path}::{line_number}::{context_lines}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            start_line = max(1, line_number - context_lines)
            end_line = min(len(lines), line_number + context_lines)
            
            context_code = ''.join(lines[start_line-1:end_line])
            imports = self.extract_imports(file_path)
            dependencies = self.analyze_dependencies(file_path)
            
            location = SourceLocation(
                file_path=file_path,
                line_number=start_line,
                end_line_number=end_line,
                module_name=file_path.stem
            )
            
            context = SourceContext(
                location=location,
                source_code=context_code,
                imports=imports,
                dependencies=dependencies
            )
            
            self._cache[cache_key] = context
            return context
            
        except (IOError, IndexError) as e:
            logger.debug(f"Error getting source context for {file_path}: {e}")
            return None 