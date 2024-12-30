from typing import List
import logging

def extract_functions(self, code: str) -> List[str]:
    """Extract function names from JavaScript code."""
    try:
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        functions = []
        
        # Get all function declarations
        for node in root_node.children:
            if node.type == "function_declaration":
                functions.append(node.child_by_field_name("name").text.decode("utf8"))
            elif node.type == "class_declaration":
                # Get class name
                class_name = node.child_by_field_name("name").text.decode("utf8")
                
                # Get class methods
                for child in node.children:
                    if child.type == "class_body":
                        for method in child.children:
                            if method.type == "method_definition":
                                name = method.child_by_field_name("name")
                                if name:
                                    method_name = name.text.decode("utf8")
                                    if method_name != "constructor":
                                        functions.append(f"{class_name}.{method_name}")
                            elif method.type == "constructor":
                                functions.append(f"{class_name}.constructor")
                            
        return functions
    except Exception as e:
        logging.error(f"Failed to parse JavaScript code: {e}")
        return [] 