# Test Integration Plan

## Overview
Add the ability to run tests and extract code from failing tests, with an optional feature to include related source code.

## Features

### 1. Basic Test Integration (`--tests`)
Run tests and extract code from failing tests.

**Command Example:**
```bash
cpai --tests "pytest"
```

**Implementation:**
- Add `--tests` argument to accept test command
- Run test command with JSON output enabled
- Parse JSON output to find failing tests
- Extract and concatenate failing test code
- Output in standard cpai format

**Technical Details:**
- Use pytest's `--json-report` flag
- Handle test command execution and output capture
- Extract file paths and test names from JSON
- Read and format test code

### 2. Source Code Integration (`--include-source`)
Additionally include the source code being tested.

**Command Example:**
```bash
cpai --tests "pytest" --include-source
```

**Implementation:**
- Parse test files to find imports and references
- Trace dependencies to source files
- Include relevant source code in output
- Group related test and source code together

**Technical Details:**
- Use AST parsing to analyze test files
- Track imports and function calls
- Map test functions to source code
- Handle relative and absolute imports

## Build Steps

### Phase 1: Basic Test Integration
1. Add `--tests` CLI argument
2. Add pytest-json-report dependency handling
3. Implement test command execution
4. Add JSON output parsing
5. Implement test code extraction
6. Format and output test code
7. Add error handling for test execution

### Phase 2: Source Integration
1. Add `--include-source` CLI argument
2. Implement AST parsing for test files
3. Add import and reference tracking
4. Implement source file resolution
5. Add source code extraction
6. Update output formatting
7. Add error handling for missing files

## Implementation Notes

### Test Command Execution
```python
def run_tests(command: str) -> dict:
    # Add --json-report flag
    full_command = f"{command} --json-report"
    result = subprocess.run(full_command, shell=True, capture_output=True)
    return load_json_report()
```

### Test Code Extraction
```python
def extract_test_code(test_results: dict) -> List[str]:
    failing_tests = []
    for test in test_results['tests']:
        if test['outcome'] == 'failed':
            code = extract_test_function(test['nodeid'])
            failing_tests.append(code)
    return failing_tests
```

### Source Code Analysis (Phase 2)
```python
def analyze_test_file(file_path: str) -> List[str]:
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(n.name for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    
    return resolve_imports(imports)
```

## Error Handling
- Handle missing pytest-json-report
- Handle test command failures
- Handle file read/write errors
- Handle AST parsing errors
- Handle missing source files

## Output Format
```markdown
## Failing Tests

### test_file.py::test_function
```python
def test_function():
    # Test code here
```

### Source: source_file.py (When --include-source is used)
```python
def source_function():
    # Source code here
```
```

## Future Considerations
- Support for other test runners (unittest, nose, etc.)
- Smarter source code inclusion (only relevant functions)
- Test coverage information
- Stack trace integration 