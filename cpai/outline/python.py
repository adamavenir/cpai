"""Python-specific outline extractor."""
import ast
import logging
from typing import List
from .base import OutlineExtractor, FunctionInfo


class PythonOutlineExtractor(OutlineExtractor):
    """Extract outline information from Python files."""

    def extract_functions(self, content: str) -> List[FunctionInfo]:
        """Extract function information from Python content."""
        try:
            # Remove any leading/trailing whitespace that might cause indentation issues
            content = content.strip()
            tree = ast.parse(content)
            
            functions = self._extract_functions(tree)
            
        except SyntaxError as e:
            logging.error(f"Failed to parse Python code: {e}")
        except Exception as e:
            logging.error(f"Failed to parse Python code: {e}")
        
        return functions

    def _extract_functions(self, node, parent_name=''):
        """Extract function definitions from an AST node."""
        functions = []
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                name = child.name
                if parent_name:
                    name = f"{parent_name}.{name}"
                
                # Skip private functions and test functions
                if (name.startswith('_') and name != '__init__' or 
                    name.startswith('test_') or
                    name == 'setUp' or
                    name == 'tearDown'):
                    continue
                
                # Get function parameters
                params = []
                for arg in child.args.args:
                    params.append(arg.arg)
                parameters = ', '.join(params)
                
                functions.append(FunctionInfo(
                    name=name,
                    line_number=child.lineno,
                    parameters=parameters,
                    leading_comment=ast.get_docstring(child)
                ))
                
            elif isinstance(child, ast.ClassDef):
                if not child.name.startswith('_'):
                    class_name = child.name
                    if parent_name:
                        class_name = f"{parent_name}.{class_name}"
                    # Don't add the class itself as a function
                    functions.extend(self._extract_functions(child, class_name))
        
        return functions

    def supports_file(self, filename: str) -> bool:
        """Check if this extractor supports the given filename."""
        return filename.endswith('.py')
