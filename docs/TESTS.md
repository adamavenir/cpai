# Testing Guide

## Understanding Test Failures

When encountering test failures, follow these principles to debug and fix them effectively:

### 1. Understand the Expected vs. Actual Behavior

The JavaScript parser case taught us that sometimes test failures occur because the test's expectations don't match the actual (and correct) behavior of the code. For example:

- The parser correctly prefixed class methods with their class name (e.g., `MyClass.myMethod`)
- But the tests were looking for bare method names (e.g., `myMethod`)
- The solution was to update the tests to match the correct behavior, not change the implementation

### 2. Work Scientifically

1. **Focus on One Test**: Fix one failing test at a time. Don't try to fix multiple failures simultaneously.
2. **Investigate, Don't Guess**: Use tools like:
   - Direct parser output inspection
   - Debug logging
   - Reading the implementation code
   - Creating isolated test cases in temporary files (for manual debugging)
3. **Make Atomic Changes**: Make small, focused changes based on what you learn.
4. **Run All Tests**: After each change, run the full test suite to ensure you haven't introduced regressions.

### 3. Debugging Tools

When debugging parser behavior:
1. **Manual Testing**: Create temporary files with isolated test cases
   - Useful for running the parser directly and seeing raw output
   - Remember to clean up temporary files after debugging
2. **Direct Inspection**: Run tools directly to see their output
   - Example: `echo "class Test {}" | node javascript_parser.js`
3. **Test Input Isolation**: Extract test cases from failing tests
   - Helps identify if the issue is in the test or the implementation
   - Allows for focused debugging without test framework overhead

### 4. Verify Tool Output

When working with tools that parse or transform code:

1. Test the tool directly (e.g., running the parser on a test case)
2. Compare the actual output with test expectations
3. Look for patterns in the differences
4. Consider whether the tool or the test needs to change

### 5. Common Test Fixes

1. **Update Test Expectations**: If the implementation is correct but tests have wrong expectations
2. **Fix Implementation**: If the tests correctly specify the desired behavior
3. **Add Missing Cases**: If tests don't cover important scenarios
4. **Remove Redundant Tests**: If tests are duplicating coverage or testing deprecated behavior

### 6. Test Maintenance

- Keep tests consistent with each other
- Document test patterns and conventions
- Update related tests when fixing one test
- Consider the impact on other tests when making changes

## JavaScript Parser Specifics

The JavaScript/TypeScript parser has some specific behaviors to be aware of:

1. **Class Methods**:
   - Methods are prefixed with their class name
   - Format: `ClassName.methodName`
   - Includes constructors: `ClassName.constructor`

2. **Export Information**:
   - Tracks both named exports (`export`) and default exports (`export default`)
   - Available via `is_export` and `is_default_export` flags

3. **Function Types**:
   - Regular functions
   - Arrow functions
   - Class methods
   - Constructors
   - Each may have different naming patterns

## Test Suite Organization

The test suite is organized into several files:

- `test_javascript.py`: JavaScript-specific parsing tests
- `test_typescript.py`: TypeScript-specific parsing tests
- `test_tree.py`: Tree structure representation tests
- Each focuses on different aspects of the functionality 