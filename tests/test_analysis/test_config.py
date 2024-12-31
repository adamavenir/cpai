"""Tests for test analysis configuration."""

import os
import pytest
from pathlib import Path
from cpai.test_analysis.config import TestAnalysisConfig


def test_default_config():
    """Test default configuration values."""
    config = TestAnalysisConfig()
    assert config.max_dependency_depth == 3
    assert config.cache_size_mb == 100
    assert config.parallel_workers == 4
    assert config.context_lines == 5
    assert config.include_source is True
    assert config.include_fixtures is True
    assert config.output_format == "markdown"
    assert config.silent is False
    assert config.notree is False


def test_config_validation():
    """Test configuration validation."""
    # Test valid config
    config = TestAnalysisConfig()
    config.validate()  # Should not raise
    
    # Test invalid max_dependency_depth
    config = TestAnalysisConfig(max_dependency_depth=0)
    with pytest.raises(ValueError, match="max_dependency_depth must be >= 1"):
        config.validate()
    
    # Test invalid cache_size_mb
    config = TestAnalysisConfig(cache_size_mb=0)
    with pytest.raises(ValueError, match="cache_size_mb must be >= 1"):
        config.validate()
    
    # Test invalid output_format
    config = TestAnalysisConfig(output_format="invalid")
    with pytest.raises(ValueError, match="output_format must be one of"):
        config.validate()


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    env_vars = {
        "TEST_ANALYSIS_MAX_DEPTH": "5",
        "TEST_ANALYSIS_CACHE_SIZE": "200",
        "TEST_ANALYSIS_WORKERS": "8",
        "TEST_ANALYSIS_CONTEXT_LINES": "10",
        "TEST_ANALYSIS_INCLUDE_SOURCE": "0",
        "TEST_ANALYSIS_INCLUDE_FIXTURES": "0",
        "TEST_ANALYSIS_OUTPUT_FORMAT": "json",
        "TEST_ANALYSIS_CACHE_DIR": "/tmp/cache",
        "TEST_ANALYSIS_SILENT": "1",
        "TEST_ANALYSIS_NOTREE": "1",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    config = TestAnalysisConfig.from_env()
    assert config.max_dependency_depth == 5
    assert config.cache_size_mb == 200
    assert config.parallel_workers == 8
    assert config.context_lines == 10
    assert config.include_source is False
    assert config.include_fixtures is False
    assert config.output_format == "json"
    assert config.cache_dir == Path("/tmp/cache")
    assert config.silent is True
    assert config.notree is True


def test_config_from_pytest_ini(tmp_path):
    """Test configuration from pytest.ini file."""
    ini_path = tmp_path / "pytest.ini"
    ini_content = """
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test
python_functions = test_*
"""
    ini_path.write_text(ini_content)
    
    config = TestAnalysisConfig.from_pytest_ini(ini_path)
    assert "testpaths" in config.pytest_ini_options
    assert config.pytest_ini_options["testpaths"] == "tests"
    assert config.pytest_ini_options["python_files"] == "test_*.py"


def test_cache_dir_creation(tmp_path):
    """Test cache directory creation."""
    config = TestAnalysisConfig(cache_dir=tmp_path / "test_cache")
    assert not config.cache_dir.exists()
    
    config.create_cache_dir()
    assert config.cache_dir.exists()
    assert config.cache_dir.is_dir()


def test_output_flags():
    """Test output control flags."""
    # Test default flags
    config = TestAnalysisConfig()
    assert not config.silent
    assert not config.notree
    
    # Test setting flags
    config = TestAnalysisConfig(silent=True, notree=True)
    assert config.silent
    assert config.notree
    
    # Test mixing flags
    config = TestAnalysisConfig(silent=True, notree=False)
    assert config.silent
    assert not config.notree 