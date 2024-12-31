"""Tests for the pytest plugin integration."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from cpai.test_analysis.config import TestAnalysisConfig
from cpai.test_analysis.plugin import TestAnalysisPlugin, pytest_configure
from cpai.test_analysis.extractor import TestFailure, TestLocation


@pytest.fixture
def config():
    """Create a test configuration."""
    return TestAnalysisConfig()


@pytest.fixture
def plugin(config):
    """Create a plugin instance."""
    return TestAnalysisPlugin(config)


def test_plugin_initialization(plugin):
    """Test that plugin initializes correctly."""
    assert len(plugin.failures) == 0
    assert isinstance(plugin._current_test_info, dict)


def test_create_detailed_report(plugin):
    """Test creation of detailed report from pytest objects."""
    # Mock pytest objects
    item = Mock()
    item.nodeid = "tests/test_example.py::test_something"
    
    report = Mock()
    report.location = ("tests/test_example.py", 42, "test_something")
    report.longrepr = "Test failed"
    
    detailed = plugin._create_detailed_report(item, report)
    assert detailed.nodeid == "tests/test_example.py::test_something"
    assert detailed.location == ("tests/test_example.py", 42, "test_something")
    assert detailed.longrepr == "Test failed"
    assert len(detailed.failed) == 1
    assert detailed.failed[0] == detailed
    assert detailed.error_message == "Test failed"


def test_pytest_runtest_makereport_success(plugin):
    """Test handling of successful test reports."""
    # Mock successful test
    item = Mock()
    report = Mock()
    report.when = "call"
    report.failed = False
    
    # Create a mock outcome
    outcome = Mock()
    outcome.get_result.return_value = report
    
    # Run through generator
    gen = plugin.pytest_runtest_makereport(item, Mock())
    next(gen)
    try:
        gen.send(outcome)
    except StopIteration:
        pass  # This is expected
    
    # Should not record any failures
    assert len(plugin.get_failures()) == 0


def test_pytest_runtest_makereport_failure(plugin):
    """Test handling of failed test reports."""
    # Mock failed test
    item = Mock()
    item.nodeid = "tests/test_example.py::test_failed"
    
    report = Mock()
    report.when = "call"
    report.failed = True
    report.location = ("tests/test_example.py", 42, "test_failed")
    report.longrepr = Mock()
    report.longrepr.reprcrash = Mock()
    report.longrepr.reprcrash.path = "tests/test_example.py"
    report.longrepr.reprcrash.lineno = 42
    report.longrepr.reprcrash.message = "assertion failed"
    
    # Create a mock outcome
    outcome = Mock()
    outcome.get_result.return_value = report
    
    # Mock the extractor to return a known failure
    failure = TestFailure(
        location=TestLocation(
            file_path=Path("tests/test_example.py"),
            line_number=42,
            function_name="test_failed"
        ),
        error_message="assertion failed",
        traceback="tests/test_example.py:42: assertion failed",
        test_source="def test_failed(): assert False"
    )
    
    with patch.object(plugin.extractor, 'extract_failing_tests', return_value=[failure]):
        # Run through generator
        gen = plugin.pytest_runtest_makereport(item, Mock())
        next(gen)
        try:
            gen.send(outcome)
        except StopIteration:
            pass  # This is expected
    
    # Should record one failure
    failures = plugin.get_failures()
    assert len(failures) == 1
    assert failures[0] == failure


def test_plugin_registration(pytestconfig):
    """Test that the plugin is properly registered with pytest."""
    plugin = pytestconfig.pluginmanager.get_plugin("testanalysis")
    assert plugin is not None
    assert isinstance(plugin, TestAnalysisPlugin)


def test_actual_test_failure(pytestconfig):
    """Test that an actual failing test is captured."""
    plugin = pytestconfig.pluginmanager.get_plugin("testanalysis")
    assert plugin is not None
    
    # Reset the failures list
    plugin.failures = []
    
    # Create a failing test
    item = Mock()
    item.nodeid = "tests/test_plugin.py::test_actual_test_failure"
    
    report = Mock()
    report.when = "call"
    report.failed = True
    report.location = ("tests/test_plugin.py", 42, "test_actual_test_failure")
    report.longrepr = Mock()
    report.longrepr.reprcrash = Mock()
    report.longrepr.reprcrash.path = "tests/test_plugin.py"
    report.longrepr.reprcrash.lineno = 42
    report.longrepr.reprcrash.message = "intentional failure"
    
    # Create an outcome
    outcome = Mock()
    outcome.get_result.return_value = report
    
    # Run through the plugin's hook
    gen = plugin.pytest_runtest_makereport(item, Mock())
    next(gen)
    try:
        gen.send(outcome)
    except StopIteration:
        pass  # This is expected
    
    # Check that the failure was captured
    failures = plugin.get_failures()
    assert len(failures) == 1
    assert failures[0].error_message == "intentional failure" 