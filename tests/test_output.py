import os
import pytest
import shutil
from cpai.main import process_files
from cpai.formatter import generate_tree
from cpai.outline.base import OutlineExtractor

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def setup_module():
    """Set up test data directory."""
    os.makedirs(os.path.join(TEST_DATA_DIR, 'javascript/components'), exist_ok=True)
    os.makedirs(os.path.join(TEST_DATA_DIR, 'python/data'), exist_ok=True)
    os.makedirs(os.path.join(TEST_DATA_DIR, 'python/tests'), exist_ok=True)

    # Create test files
    with open(os.path.join(TEST_DATA_DIR, 'javascript/components/Button.jsx'), 'w') as f:
        f.write("""
import React from 'react';

export default function Button({ onClick, children }) {
    return (
        <button onClick={onClick}>
            {children}
        </button>
    );
}
""")

    with open(os.path.join(TEST_DATA_DIR, 'python/data/models.py'), 'w') as f:
        f.write("""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

@dataclass
class BaseModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class Category(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            **super().to_dict(),
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id
        }

@dataclass
class Product(BaseModel):
    name: str
    price: float
    category_id: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    in_stock: bool = True

    def to_dict(self) -> Dict:
        return {
            **super().to_dict(),
            'name': self.name,
            'price': self.price,
            'category_id': self.category_id,
            'description': self.description,
            'tags': self.tags,
            'in_stock': self.in_stock
        }

    @property
    def is_available(self) -> bool:
        return self.in_stock and self.price > 0

    def apply_discount(self, percentage: float) -> None:
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        self.price *= (1 - percentage / 100)
""")

def teardown_module():
    """Clean up test data directory."""
    shutil.rmtree(TEST_DATA_DIR)

def test_tree_output_format():
    """Test that the tree output matches the expected format."""
    test_files = [
        os.path.join(TEST_DATA_DIR, 'javascript/components/Button.jsx'),
        os.path.join(TEST_DATA_DIR, 'python/data/models.py')
    ]
    
    tree_output = generate_tree(test_files)
    
    # Check directory structure section
    assert '```' in tree_output
    assert 'javascript/components/Button.jsx' in tree_output
    assert 'python/data/models.py' in tree_output

def test_file_processing():
    """Test that file processing works correctly."""
    test_files = [
        os.path.join(TEST_DATA_DIR, 'python/data/models.py')
    ]
    
    output = process_files(test_files)
    assert 'models.py' in output
    assert 'class' in output['models.py']['content'].lower()
    assert 'def' in output['models.py']['content'].lower()

def test_exclusion_patterns():
    """Test that exclusion patterns work correctly."""
    test_files = [
        os.path.join(TEST_DATA_DIR, 'javascript/components/Button.test.jsx'),
        os.path.join(TEST_DATA_DIR, 'python/tests/test_models.py'),
        os.path.join(TEST_DATA_DIR, 'python/data/models.py')
    ]
    
    config = {
        'exclude': ['**/*.test.*', '**/tests/**']
    }
    
    # Only models.py should be included
    output = process_files(test_files, config=config)
    assert 'test_models.py' not in output
    assert 'Button.test.jsx' not in output
    assert 'models.py' in output

def test_custom_config():
    """Test that custom configuration works correctly."""
    config = {
        'include': ['python/data'],
        'exclude': ['**/*.test.*', '**/tests/**'],
        'fileExtensions': ['.py']
    }
    
    test_files = [
        os.path.join(TEST_DATA_DIR, 'javascript/components/Button.jsx'),  # Should be excluded (extension)
        os.path.join(TEST_DATA_DIR, 'python/data/models.py'),  # Should be included
        os.path.join(TEST_DATA_DIR, 'python/tests/test_models.py')  # Should be excluded (tests)
    ]
    
    output = process_files(test_files, config=config)
    assert 'Button.jsx' not in output
    assert 'test_models.py' not in output
    assert 'models.py' in output
