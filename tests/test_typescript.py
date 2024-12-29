"""Tests for JavaScript/TypeScript outline extractor."""
import pytest
from cpai.outline.javascript import JavaScriptOutlineExtractor

def test_javascript_supports_file():
    extractor = JavaScriptOutlineExtractor()
    # JavaScript files
    assert extractor.supports_file("test.js") is True
    assert extractor.supports_file("test.jsx") is True
    # TypeScript files
    assert extractor.supports_file("test.ts") is True
    assert extractor.supports_file("test.tsx") is True
    # Other files
    assert extractor.supports_file("test.py") is False
    assert extractor.supports_file("javascript_parser.js") is False

def test_extract_typescript_functions():
    extractor = JavaScriptOutlineExtractor()
    content = """
// User interface
interface User {
    name: string;
    age: number;
}

/**
 * A service for managing users
 */
export class UserService {
    private users: User[] = [];
    
    /**
     * Add a new user
     */
    addUser(user: User): void {
        this.users.push(user);
    }
    
    getUsers(): User[] {
        return this.users;
    }
}

// Utility function
export function formatUser(user: User): string {
    return `${user.name} (${user.age})`;
}

// Default export arrow function
const processUser = (user: User): void => {
    console.log(formatUser(user));
};
export default processUser;
"""
    
    functions = extractor.extract_functions(content)
    assert len(functions) == 5  # UserService class, addUser, getUsers, formatUser, processUser
    
    # Check class method
    user_service = next(f for f in functions if f.name == "UserService")
    assert user_service.line_number > 0
    assert "service for managing users" in user_service.leading_comment
    assert user_service.is_export
    assert not user_service.is_default_export
    
    # Check instance method
    add_user = next(f for f in functions if f.name == "UserService.addUser")
    assert add_user.line_number > 0
    assert "user: User" in add_user.parameters
    assert "Add a new user" in add_user.leading_comment
    
    # Check instance method
    get_users = next(f for f in functions if f.name == "UserService.getUsers")
    assert get_users.line_number > 0
    
    # Check utility function
    format_user = next(f for f in functions if f.name == "formatUser")
    assert format_user.line_number > 0
    assert "user: User" in format_user.parameters
    assert format_user.is_export
    assert not format_user.is_default_export
    
    # Check arrow function
    process_user = next(f for f in functions if f.name == "processUser")
    assert process_user.line_number > 0
    assert "user: User" in process_user.parameters
    assert process_user.is_export
    assert process_user.is_default_export

def test_extract_javascript_functions():
    extractor = JavaScriptOutlineExtractor()
    content = """
/**
 * User service for managing application users
 */
class UserService {
    constructor(config) {
        this.config = config;
    }

    /**
     * Add a new user to the system
     */
    addUser(user) {
        // Implementation
    }
}

// Utility function
function formatUser(user) {
    return `${user.name}`;
}

// Arrow function
const processUser = user => {
    console.log(formatUser(user));
};
"""
    
    functions = extractor.extract_functions(content)
    assert len(functions) == 5  # UserService, constructor, addUser, formatUser, processUser
    
    # Check class
    user_service = next(f for f in functions if f.name == "UserService")
    assert user_service.line_number > 0
    assert "User service for managing" in user_service.leading_comment
    
    # Check constructor
    constructor = next(f for f in functions if f.name == "UserService.constructor")
    assert constructor.line_number > 0
    assert "config" in constructor.parameters
    
    # Check instance method
    add_user = next(f for f in functions if f.name == "UserService.addUser")
    assert add_user.line_number > 0
    assert "user" in add_user.parameters
    assert "Add a new user" in add_user.leading_comment
    
    # Check utility function
    format_user = next(f for f in functions if f.name == "formatUser")
    assert format_user.line_number > 0
    assert "user" in format_user.parameters

def test_extract_typescript_with_decorators():
    extractor = JavaScriptOutlineExtractor()
    content = """
import { Controller, Get } from '@nestjs/common';

@Controller('users')
export class UsersController {
    /**
     * Get all users
     */
    @Get()
    getAllUsers() {
        return [];
    }

    @Get(':id')
    getUserById(@Param('id') id: string) {
        return { id };
    }
}
"""
    
    functions = extractor.extract_functions(content)
    assert len(functions) == 3  # UsersController class and two methods
    
    controller = next(f for f in functions if f.name == "UsersController")
    assert controller.line_number > 0
    assert controller.is_export
    assert not controller.is_default_export
    
    get_all = next(f for f in functions if f.name == "UsersController.getAllUsers")
    assert get_all.line_number > 0
    assert "Get all users" in get_all.leading_comment
    
    get_by_id = next(f for f in functions if f.name == "UsersController.getUserById")
    assert get_by_id.line_number > 0
    assert "id: string" in get_by_id.parameters
