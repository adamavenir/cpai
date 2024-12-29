import os
import pytest
from cpai.outline.base import OutlineExtractor
from cpai.outline.javascript import JavaScriptOutlineExtractor
from cpai.outline.python import PythonOutlineExtractor
from cpai.outline.solidity import SolidityOutlineExtractor
from cpai.outline.rust import RustOutlineExtractor

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def read_test_file(filename):
    """Helper to read test files."""
    with open(os.path.join(TEST_DATA_DIR, filename), 'r') as f:
        return f.read()

@pytest.fixture
def js_extractor():
    return JavaScriptOutlineExtractor()

@pytest.fixture
def py_extractor():
    return PythonOutlineExtractor()

@pytest.fixture
def sol_extractor():
    return SolidityOutlineExtractor()

@pytest.fixture
def rust_extractor():
    return RustOutlineExtractor()

def test_javascript_basic_function(js_extractor):
    content = """
    function myFunction() {
        // Function content
    }
    """
    functions = js_extractor.extract_functions(content)
    assert len(functions) == 1
    assert functions[0].name == 'myFunction'
    assert functions[0].node_type == 'function'

def test_javascript_arrow_function(js_extractor):
    content = """
    const myArrowFunction = () => {
        // Function content
    };
    """
    functions = js_extractor.extract_functions(content)
    assert len(functions) == 1
    assert functions[0].name == 'myArrowFunction'
    assert functions[0].node_type == 'function'

def test_javascript_class_method(js_extractor):
    content = """
    class MyClass {
        constructor() {}
        
        myMethod() {
            // Method content
        }
    }
    """
    functions = js_extractor.extract_functions(content)
    assert len(functions) == 3
    assert 'MyClass' in [f.name for f in functions]
    assert 'MyClass.constructor' in [f.name for f in functions]
    assert 'MyClass.myMethod' in [f.name for f in functions]

def test_python_class_method(py_extractor):
    content = """
    class MyClass:
        def my_method(self):
            pass
    """
    functions = py_extractor.extract_functions(content)
    assert len(functions) == 2
    assert 'MyClass' in [f.name for f in functions]
    assert 'MyClass.my_method' in [f.name for f in functions]

def test_solidity_contract(sol_extractor):
    content = """
    contract MyContract {
        function myFunction() public {
            // Function content
        }
    }
    """
    functions = sol_extractor.extract_functions(content)
    assert len(functions) == 2
    assert 'MyContract' in [f.name for f in functions]
    assert 'MyContract.myFunction' in [f.name for f in functions]

def test_rust_impl(rust_extractor):
    content = """
    impl MyStruct {
        pub fn new() -> Self {
            Self {}
        }

        pub fn method(&self) {
        }

        fn private_method(&self) {
        }
    }
    """
    functions = rust_extractor.extract_functions(content)
    assert len(functions) == 3
    assert 'MyStruct.new' in [f.name for f in functions]
    assert 'MyStruct.method' in [f.name for f in functions]
    assert 'MyStruct.private_method' in [f.name for f in functions]
