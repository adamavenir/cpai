"""Configuration management for test analysis."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass  # type: ignore[misc] # Ignore pytest collection warning
class TestAnalysisConfig:
    """Configuration for test analysis functionality."""
    
    # Performance settings
    max_dependency_depth: int = 3
    cache_size_mb: int = 100
    parallel_workers: int = 4
    
    # Analysis settings
    context_lines: int = 5
    include_source: bool = True
    include_fixtures: bool = True
    max_file_size_mb: int = 10
    
    # Output settings
    output_format: str = "markdown"
    output_file: Optional[Path] = None
    silent: bool = False  # Suppress all output except content
    notree: bool = False  # Skip tree output, only show code with headers
    
    # Cache settings
    cache_dir: Path = field(default_factory=lambda: Path(".cache/test_analysis"))
    cache_ttl_minutes: int = 60
    
    # Pytest integration
    pytest_args: List[str] = field(default_factory=list)
    pytest_ini_options: Dict[str, str] = field(default_factory=dict)
    
    # Workspace settings
    workspace_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "TestAnalysisConfig":
        """Create config from environment variables."""
        import os
        
        return cls(
            max_dependency_depth=int(os.getenv("TEST_ANALYSIS_MAX_DEPTH", "3")),
            cache_size_mb=int(os.getenv("TEST_ANALYSIS_CACHE_SIZE", "100")),
            parallel_workers=int(os.getenv("TEST_ANALYSIS_WORKERS", "4")),
            context_lines=int(os.getenv("TEST_ANALYSIS_CONTEXT_LINES", "5")),
            include_source=os.getenv("TEST_ANALYSIS_INCLUDE_SOURCE", "1") == "1",
            include_fixtures=os.getenv("TEST_ANALYSIS_INCLUDE_FIXTURES", "1") == "1",
            output_format=os.getenv("TEST_ANALYSIS_OUTPUT_FORMAT", "markdown"),
            cache_dir=Path(os.getenv("TEST_ANALYSIS_CACHE_DIR", ".cache/test_analysis")),
            silent=os.getenv("TEST_ANALYSIS_SILENT", "0") == "1",
            notree=os.getenv("TEST_ANALYSIS_NOTREE", "0") == "1",
            workspace_dir=os.getenv("TEST_ANALYSIS_WORKSPACE_DIR")
        )
    
    @classmethod
    def from_pytest_ini(cls, ini_path: Path) -> "TestAnalysisConfig":
        """Create config from pytest.ini file."""
        import configparser
        
        config = configparser.ConfigParser()
        config.read(ini_path)
        
        if "pytest" not in config:
            return cls()
            
        pytest_section = dict(config["pytest"].items())
        return cls(pytest_ini_options=pytest_section)
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if self.max_dependency_depth < 1:
            raise ValueError("max_dependency_depth must be >= 1")
        if self.cache_size_mb < 1:
            raise ValueError("cache_size_mb must be >= 1")
        if self.parallel_workers < 1:
            raise ValueError("parallel_workers must be >= 1")
        if self.context_lines < 0:
            raise ValueError("context_lines must be >= 0")
        if self.output_format not in ["markdown", "json", "html"]:
            raise ValueError("output_format must be one of: markdown, json, html")
            
    def create_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True) 