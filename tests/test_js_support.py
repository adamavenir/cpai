"""Tests for JavaScript test runner support."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from cpai.test_utils import (
    run_test_command,
    extract_js_test_function,
    parse_test_results,
    extract_failing_tests
)
from cpai.source_analysis import (
    extract_imports,
    find_source_file,
    analyze_test_file,
    extract_source_code
)

def test_run_jest_command():
    """Test running Jest command with JSON output."""
    mock_jest_output = {
        'testResults': [
            {
                'name': 'src/components/__tests__/Button.test.tsx',
                'assertionResults': [
                    {
                        'title': 'renders button with text',
                        'status': 'failed',
                        'failureMessages': ['Expected text to be "Click me!" but got "Click me"']
                    }
                ]
            }
        ]
    }
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = json.dumps(mock_jest_output)
        mock_run.return_value.stderr = ''
        
        # Test that --json flag is added
        result = run_test_command('jest')
        mock_run.assert_called_with(['jest', '--json'], capture_output=True, text=True)
        
        # Test that output is parsed correctly
        assert result['runner'] == 'jest'
        assert result['results'] == mock_jest_output

def test_run_vitest_command():
    """Test running Vitest command with JSON reporter."""
    mock_vitest_output = {
        'testResults': [
            {
                'name': 'src/components/Button.test.ts',
                'tasks': [
                    {
                        'name': 'renders correctly',
                        'result': {
                            'state': 'fail',
                            'error': {
                                'message': 'Expected button to have text'
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = json.dumps(mock_vitest_output)
        mock_run.return_value.stderr = ''
        
        # Test that --reporter=json flag is added
        result = run_test_command('vitest')
        mock_run.assert_called_with(['vitest', '--reporter=json'], capture_output=True, text=True)
        
        # Test that output is parsed correctly
        assert result['runner'] == 'vitest'
        assert result['results'] == mock_vitest_output

def test_extract_js_test_function():
    """Test extracting test functions from JavaScript/TypeScript files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / 'button.test.tsx'
        
        # Test various test function patterns
        test_patterns = {
            # Arrow function
            '''
            test('renders button', () => {
                render(<Button>Click me</Button>)
            })
            ''': 'renders button',
            
            # Async arrow function
            '''
            test('loads data', async () => {
                const data = await fetchData()
                expect(data).toBeDefined()
            })
            ''': 'loads data',
            
            # Regular function
            '''
            test('handles click', function() {
                const button = screen.getByRole('button')
                fireEvent.click(button)
            })
            ''': 'handles click',
            
            # it() syntax
            '''
            it('should work', () => {
                expect(true).toBe(true)
            })
            ''': 'should work',
            
            # Nested in describe
            '''
            describe('Button', () => {
                it('renders text', () => {
                    expect(screen.getByText('Click')).toBeInTheDocument()
                })
            })
            ''': 'renders text'
        }
        
        for test_content, function_name in test_patterns.items():
            test_file.write_text(test_content)
            extracted = extract_js_test_function(str(test_file), function_name)
            assert extracted is not None
            assert function_name in extracted
            assert '{' in extracted and '}' in extracted

def test_parse_jest_results():
    """Test parsing Jest test results."""
    jest_results = {
        'runner': 'jest',
        'results': {
            'testResults': [
                {
                    'name': 'button.test.tsx',
                    'assertionResults': [
                        {
                            'title': 'test one',
                            'status': 'failed',
                            'failureMessages': ['Error message one']
                        },
                        {
                            'title': 'test two',
                            'status': 'passed'
                        }
                    ]
                }
            ]
        }
    }
    
    parsed = parse_test_results(jest_results)
    assert len(parsed) == 1  # Only failed tests
    assert parsed[0]['file'] == 'button.test.tsx'
    assert parsed[0]['function'] == 'test one'
    assert parsed[0]['message'] == 'Error message one'

def test_parse_vitest_results():
    """Test parsing Vitest test results."""
    vitest_results = {
        'runner': 'vitest',
        'results': {
            'testResults': [
                {
                    'name': 'input.test.ts',
                    'tasks': [
                        {
                            'name': 'test one',
                            'result': {
                                'state': 'fail',
                                'error': {
                                    'message': 'Failed assertion'
                                }
                            }
                        },
                        {
                            'name': 'test two',
                            'result': {
                                'state': 'pass'
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    parsed = parse_test_results(vitest_results)
    assert len(parsed) == 1  # Only failed tests
    assert parsed[0]['file'] == 'input.test.ts'
    assert parsed[0]['function'] == 'test one'
    assert parsed[0]['message'] == 'Failed assertion'

def test_extract_failing_js_tests():
    """Test extracting failing tests from JavaScript files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_dir = Path(temp_dir) / 'tests'
        test_dir.mkdir()
        test_file = test_dir / 'button.test.tsx'
        test_content = '''
        test('renders button', () => {
            render(<Button>Click me</Button>)
            expect(screen.getByRole('button')).toHaveTextContent('Click me!')
        })
        '''
        test_file.write_text(test_content)
        
        # Mock test results
        test_results = {
            'runner': 'jest',
            'results': {
                'testResults': [
                    {
                        'name': str(test_file),
                        'assertionResults': [
                            {
                                'title': 'renders button',
                                'status': 'failed',
                                'failureMessages': ['Expected text content to match']
                            }
                        ]
                    }
                ]
            }
        }
        
        failing_tests = extract_failing_tests(test_results)
        assert len(failing_tests) == 1
        assert failing_tests[0]['file'] == str(test_file)
        assert failing_tests[0]['function'] == 'renders button'
        assert 'render(<Button>' in failing_tests[0]['code']
        assert 'Expected text content to match' in failing_tests[0]['message'] 

def test_extract_js_imports():
    """Test extracting imports from JavaScript/TypeScript files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / 'button.test.tsx'
        
        # Test various import patterns
        test_content = '''
        import React from 'react';
        import { render, screen } from '@testing-library/react';
        import userEvent from '@testing-library/user-event';
        import type { ButtonProps } from '../types';
        import Button from '../components/Button';
        import { useTheme } from '../../hooks';
        import styles from './Button.module.css';
        
        // Dynamic imports
        const utils = await import('./test-utils');
        
        // Require (CommonJS)
        const config = require('../config');
        '''
        
        test_file.write_text(test_content)
        imports = extract_imports(str(test_file))
        
        # Check that all imports are found
        assert 'react' in imports
        assert '@testing-library/react' in imports
        assert '@testing-library/user-event' in imports
        assert '../types' in imports
        assert '../components/Button' in imports
        assert '../../hooks' in imports
        assert './Button.module.css' in imports
        assert './test-utils' in imports
        assert '../config' in imports

def test_find_js_source_file():
    """Test finding source files for JavaScript/TypeScript imports."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source files
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        components_dir = src_dir / 'components'
        components_dir.mkdir()
        
        # Create various module formats
        (components_dir / 'Button.tsx').write_text('export const Button = () => <button/>;')
        input_dir = components_dir / 'Input'
        input_dir.mkdir()  # Create Input directory first
        (input_dir / 'index.ts').write_text('export * from "./Input";')
        (input_dir / 'Input.tsx').write_text('export const Input = () => <input/>;')
        (src_dir / 'utils.ts').write_text('export const format = (s: string) => s.trim();')
        
        # Test finding different module formats
        search_paths = [str(src_dir)]
        
        # Direct file
        button_file = find_source_file('components/Button', search_paths)
        assert button_file is not None
        assert button_file.endswith('Button.tsx')
        
        # Index file
        input_file = find_source_file('components/Input', search_paths)
        assert input_file is not None
        assert input_file.endswith('index.ts')
        
        # File in root
        utils_file = find_source_file('utils', search_paths)
        assert utils_file is not None
        assert utils_file.endswith('utils.ts')

def test_analyze_js_test_file():
    """Test analyzing JavaScript/TypeScript test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source structure
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        components_dir = src_dir / 'components'
        components_dir.mkdir()
        tests_dir = src_dir / '__tests__'
        tests_dir.mkdir()
        
        # Create source files
        button_file = components_dir / 'Button.tsx'
        button_file.write_text('''
        import React from 'react';
        import { useTheme } from '../hooks';
        import styles from './Button.module.css';
        
        export const Button = ({ children }) => {
            const theme = useTheme();
            return <button className={styles.button}>{children}</button>;
        };
        ''')
        
        hooks_file = src_dir / 'hooks.ts'
        hooks_file.write_text('''
        export const useTheme = () => {
            return { primary: 'blue' };
        };
        ''')
        
        # Create test file
        test_file = tests_dir / 'Button.test.tsx'
        test_file.write_text('''
        import { render } from '@testing-library/react';
        import { Button } from '../components/Button';
        import { useTheme } from '../hooks';
        
        test('renders button', () => {
            render(<Button>Click me</Button>);
        });
        ''')
        
        # Analyze test file
        source_files = analyze_test_file(str(test_file), test_mode=True)
        
        # Check that source files are found
        assert any('Button.tsx' in f for f in source_files.values())
        assert any('hooks.ts' in f for f in source_files.values())
        
        # Extract and check source code
        source_code = extract_source_code(source_files)
        assert len(source_code) >= 2  # Should have Button and hooks
        
        # Check source code content
        button_source = next(code for path, code in source_code.items() if 'Button.tsx' in path)
        assert 'export const Button' in button_source
        assert 'useTheme' in button_source
        
        hooks_source = next(code for path, code in source_code.items() if 'hooks.ts' in path)
        assert 'export const useTheme' in hooks_source

def test_extract_js_source_with_types():
    """Test extracting TypeScript source with type imports."""
    with tempfile.TemporaryDirectory() as temp_dir:
        src_dir = Path(temp_dir) / 'src'
        src_dir.mkdir()
        
        # Create types file
        types_file = src_dir / 'types.ts'
        types_file.write_text('''
        export interface ButtonProps {
            variant?: 'primary' | 'secondary';
            children: React.ReactNode;
        }
        
        export type Theme = {
            primary: string;
            secondary: string;
        };
        ''')
        
        # Create component using types
        button_file = src_dir / 'Button.tsx'
        button_file.write_text('''
        import type { ButtonProps } from './types';
        import { Theme } from './types';
        
        export const Button: React.FC<ButtonProps> = ({ variant = 'primary', children }) => {
            return <button className={variant}>{children}</button>;
        };
        ''')
        
        # Create test file
        test_file = src_dir / 'Button.test.tsx'
        test_file.write_text('''
        import type { ButtonProps } from './types';
        import { Button } from './Button';
        
        test('renders with props', () => {
            const props: ButtonProps = {
                variant: 'primary',
                children: 'Click me'
            };
            render(<Button {...props} />);
        });
        ''')
        
        # Analyze and extract source
        source_files = analyze_test_file(str(test_file), test_mode=True)
        print("\nSource files:", source_files)
        source_code = extract_source_code(source_files)
        print("\nSource code:", source_code)
        
        # Verify all files are found
        assert len(source_code) >= 3  # Should have types, button, and test
        
        # Check that type definitions are included
        types_source = next(code for path, code in source_code.items() if 'types.ts' in path)
        assert 'interface ButtonProps' in types_source
        assert 'type Theme' in types_source 