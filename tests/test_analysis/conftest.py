"""Test configuration for test analysis."""

import pytest
from cpai.test_analysis.config import TestAnalysisConfig
from cpai.test_analysis.plugin import TestAnalysisPlugin


@pytest.fixture(autouse=True)
def register_plugin(pytestconfig):
    """Register the test analysis plugin for all tests in this directory."""
    plugin = TestAnalysisPlugin(TestAnalysisConfig())
    if not pytestconfig.pluginmanager.get_plugin("testanalysis"):
        pytestconfig.pluginmanager.register(plugin, "testanalysis")
    return plugin 