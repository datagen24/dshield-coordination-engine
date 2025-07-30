"""Unit tests for tools base module."""

from typing import Any
from unittest.mock import patch

import pytest

from tools.base import BaseTool, ToolRegistry, tool_registry


class TestBaseTool:
    """Test the BaseTool abstract class."""

    class MockTool(BaseTool):
        """Mock tool for testing."""

        async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
            """Mock execute implementation."""
            data["processed"] = True
            return data

    def test_base_tool_initialization(self):
        """Test BaseTool initialization."""
        tool = self.MockTool("test-tool")
        assert tool.name == "test-tool"
        assert tool.config == {}
        assert tool.logger is not None

    def test_base_tool_initialization_with_config(self):
        """Test BaseTool initialization with config."""
        config = {"key": "value", "timeout": 30}
        tool = self.MockTool("test-tool", config)
        assert tool.name == "test-tool"
        assert tool.config == config

    def test_log_execution(self):
        """Test log_execution method."""
        tool = self.MockTool("test-tool")
        data = {"key1": "value1", "key2": "value2"}

        with patch.object(tool.logger, "info") as mock_info:
            tool.log_execution(data)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[1]["tool_name"] == "test-tool"
            assert "key1" in call_args[1]["data_keys"]
            assert "key2" in call_args[1]["data_keys"]

    def test_log_completion(self):
        """Test log_completion method."""
        tool = self.MockTool("test-tool")
        result = {"result1": "value1", "result2": "value2"}

        with patch.object(tool.logger, "info") as mock_info:
            tool.log_completion(result)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[1]["tool_name"] == "test-tool"
            assert "result1" in call_args[1]["result_keys"]
            assert "result2" in call_args[1]["result_keys"]

    def test_log_error(self):
        """Test log_error method."""
        tool = self.MockTool("test-tool")
        data = {"key1": "value1"}
        error = ValueError("Test error")

        with patch.object(tool.logger, "error") as mock_error:
            tool.log_error(error, data)
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert call_args[1]["tool_name"] == "test-tool"
            assert call_args[1]["error"] == "Test error"
            assert "key1" in call_args[1]["data_keys"]

    @pytest.mark.asyncio
    async def test_run_success(self):
        """Test successful run method."""
        tool = self.MockTool("test-tool")
        data = {"input": "test"}

        with (
            patch.object(tool, "log_execution") as mock_log_execution,
            patch.object(tool, "log_completion") as mock_log_completion,
            patch.object(tool, "log_error") as mock_log_error,
        ):
            result = await tool.run(data)

            mock_log_execution.assert_called_once_with(data)
            mock_log_completion.assert_called_once()
            mock_log_error.assert_not_called()
            assert result["processed"] is True
            assert result["input"] == "test"

    @pytest.mark.asyncio
    async def test_run_with_error(self):
        """Test run method with error handling."""

        class ErrorTool(BaseTool):
            """Tool that raises an error."""

            async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                """Raise an error."""
                raise ValueError("Test error")

        tool = ErrorTool("error-tool")
        data = {"input": "test"}

        with (
            patch.object(tool, "log_execution") as mock_log_execution,
            patch.object(tool, "log_completion") as mock_log_completion,
            patch.object(tool, "log_error") as mock_log_error,
        ):
            with pytest.raises(ValueError, match="Test error"):
                await tool.run(data)

            mock_log_execution.assert_called_once_with(data)
            mock_log_completion.assert_not_called()
            mock_log_error.assert_called_once()


class TestToolRegistry:
    """Test the ToolRegistry class."""

    def test_registry_initialization(self):
        """Test ToolRegistry initialization."""
        registry = ToolRegistry()
        assert registry.tools == {}

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = TestBaseTool.MockTool("test-tool")

        with patch("tools.base.logger") as mock_logger:
            registry.register(tool)

            assert "test-tool" in registry.tools
            assert registry.tools["test-tool"] == tool
            mock_logger.info.assert_called_once()

    def test_get_existing_tool(self):
        """Test getting an existing tool."""
        registry = ToolRegistry()
        tool = TestBaseTool.MockTool("test-tool")
        registry.tools["test-tool"] = tool

        result = registry.get("test-tool")
        assert result == tool

    def test_get_nonexistent_tool(self):
        """Test getting a nonexistent tool."""
        registry = ToolRegistry()

        result = registry.get("nonexistent-tool")
        assert result is None

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = TestBaseTool.MockTool("tool1")
        tool2 = TestBaseTool.MockTool("tool2")
        registry.tools["tool1"] = tool1
        registry.tools["tool2"] = tool2

        result = registry.list_tools()
        assert "tool1" in result
        assert "tool2" in result
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        registry = ToolRegistry()
        tool = TestBaseTool.MockTool("test-tool")
        registry.tools["test-tool"] = tool

        data = {"input": "test"}
        result = await registry.execute_tool("test-tool", data)

        assert result["processed"] is True
        assert result["input"] == "test"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a nonexistent tool."""
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="Tool 'nonexistent-tool' not found"):
            await registry.execute_tool("nonexistent-tool", {"data": "test"})


class TestGlobalToolRegistry:
    """Test the global tool registry instance."""

    def test_global_registry_exists(self):
        """Test that global registry exists."""
        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)

    @pytest.mark.asyncio
    async def test_global_registry_functionality(self):
        """Test global registry functionality."""
        # Clear any existing tools
        tool_registry.tools.clear()

        tool = TestBaseTool.MockTool("global-test-tool")
        tool_registry.register(tool)

        assert "global-test-tool" in tool_registry.tools
        assert tool_registry.get("global-test-tool") == tool

        data = {"input": "test"}
        result = await tool_registry.execute_tool("global-test-tool", data)

        assert result["processed"] is True
        assert result["input"] == "test"
