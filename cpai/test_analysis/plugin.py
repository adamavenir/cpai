"""Pytest plugin for test analysis."""

from typing import List, Optional, Dict, Any, Generator
import pytest
from pathlib import Path
from .extractor import TestExtractor, TestFailure
from .config import TestAnalysisConfig


class TestAnalysisPlugin:
    """Pytest plugin that collects test execution information."""

    def __init__(self, config: TestAnalysisConfig):
        """Initialize the plugin.
        
        Args:
            config: Configuration for test analysis
        """
        self.config = config
        self.extractor = TestExtractor(config)
        self.failures: List[TestFailure] = []
        self._current_test_info: Dict[str, Any] = {}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Any, call: Any) -> Generator[None, Any, None]:
        """Hook that intercepts test reports as they are created.
        
        This allows us to capture test failures in real-time.
        """
        outcome = yield
        report = outcome.get_result()

        if report.when == "call" and report.failed:
            # Create a more detailed report object that matches what our extractor expects
            detailed_report = self._create_detailed_report(item, report)
            failures = self.extractor.extract_failing_tests(detailed_report)
            self.failures.extend(failures)

    def _create_detailed_report(self, item: Any, report: Any) -> Any:
        """Create a detailed report object from pytest's report.
        
        Args:
            item: The pytest item being tested
            report: The pytest report object
            
        Returns:
            A report object compatible with our TestExtractor
        """
        class DetailedReport:
            def __init__(self, item, report):
                self.nodeid = item.nodeid
                self.location = report.location
                self.longrepr = report.longrepr
                self.failed = [self]  # Make it look like a session report
                
                # Extract error message from longrepr
                if hasattr(report.longrepr, 'reprcrash'):
                    self.error_message = report.longrepr.reprcrash.message
                elif isinstance(report.longrepr, str):
                    self.error_message = report.longrepr
                else:
                    self.error_message = str(report.longrepr)

        return DetailedReport(item, report)

    def get_failures(self) -> List[TestFailure]:
        """Get the list of test failures collected during the test run.
        
        Returns:
            List of TestFailure objects
        """
        return self.failures


@pytest.fixture
def test_analysis(request) -> TestAnalysisPlugin:
    """Fixture that provides access to the test analysis plugin.
    
    Usage:
        def test_something(test_analysis):
            # Run your test
            assert False  # This will be captured
            
    Returns:
        TestAnalysisPlugin instance
    """
    config = TestAnalysisConfig()  # You might want to customize this
    plugin = TestAnalysisPlugin(config)
    request.node.session.testanalysis = plugin  # Store for later access
    return plugin


def pytest_configure(config):
    """Pytest hook to configure the plugin.
    
    This registers our plugin with pytest.
    """
    plugin = TestAnalysisPlugin(TestAnalysisConfig())
    config.pluginmanager.register(plugin, "testanalysis")
    return plugin  # Return the plugin so it can be accessed by tests 