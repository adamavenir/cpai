import unittest
import os
import tempfile
import shutil
from cpai.outline.javascript import JavaScriptOutlineExtractor
from cpai.outline.python import PythonOutlineExtractor
from cpai.outline.solidity import SolidityOutlineExtractor
from cpai.outline.rust import RustOutlineExtractor

class TestTree(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_javascript_basic_function(self):
        """Test extracting basic JavaScript function."""
        code = """
function hello() {
    console.log('Hello');
}
"""
        extractor = JavaScriptOutlineExtractor()
        functions = extractor.extract_functions(code)
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, 'hello')

    def test_javascript_arrow_function(self):
        """Test extracting arrow function."""
        code = """
const hello = () => {
    console.log('Hello');
};
"""
        extractor = JavaScriptOutlineExtractor()
        functions = extractor.extract_functions(code)
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, 'hello')

    def test_javascript_class_method(self):
        """Test extracting class method."""
        code = """
class MyClass {
    constructor() {
        this.name = 'MyClass';
    }
    
    hello() {
        console.log('Hello from', this.name);
    }
    
    static greet() {
        console.log('Static greeting');
    }
}
"""
        extractor = JavaScriptOutlineExtractor()
        functions = extractor.extract_functions(code)
        print("\nFound functions:", [f.name for f in functions])  # Debug output
        self.assertEqual(len(functions), 3)  # constructor, hello, and greet
        self.assertEqual(functions[0].name, 'MyClass.constructor')
        self.assertEqual(functions[1].name, 'MyClass.hello')
        self.assertEqual(functions[2].name, 'MyClass.greet')

    def test_python_class_method(self):
        """Test extracting Python class method."""
        code = """
class MyClass:
    def __init__(self):
        self.name = 'MyClass'
    
    def hello(self):
        print('Hello from', self.name)
    
    @staticmethod
    def greet():
        print('Static greeting')
"""
        extractor = PythonOutlineExtractor()
        functions = extractor.extract_functions(code)
        self.assertEqual(len(functions), 3)  # __init__, hello, and greet
        self.assertEqual(functions[0].name, 'MyClass.__init__')
        self.assertEqual(functions[1].name, 'MyClass.hello')
        self.assertEqual(functions[2].name, 'MyClass.greet')

    def test_solidity_contract(self):
        """Test extracting Solidity contract functions."""
        code = """
contract MyContract {
    function hello() public view returns (string memory) {
        return "Hello";
    }
    
    function greet(string memory name) public pure returns (string memory) {
        return string(abi.encodePacked("Hello, ", name));
    }
}
"""
        extractor = SolidityOutlineExtractor()
        functions = extractor.extract_functions(code)
        self.assertEqual(len(functions), 2)  # hello and greet
        self.assertEqual(functions[0].name, 'MyContract.hello')
        self.assertEqual(functions[1].name, 'MyContract.greet')

    def test_rust_impl(self):
        """Test extracting Rust impl functions."""
        code = """
impl MyStruct {
    pub fn new() -> Self {
        MyStruct {}
    }
    
    pub fn hello(&self) {
        println!("Hello");
    }
    
    pub fn greet(name: &str) {
        println!("Hello, {}", name);
    }
}
"""
        extractor = RustOutlineExtractor()
        functions = extractor.extract_functions(code)
        self.assertEqual(len(functions), 3)  # new, hello, and greet
        self.assertEqual(functions[0].name, 'MyStruct.new')
        self.assertEqual(functions[1].name, 'MyStruct.hello')
        self.assertEqual(functions[2].name, 'MyStruct.greet')
