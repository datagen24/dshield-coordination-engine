"""Base tool class for external integrations."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseTool(ABC):
    """Base class for all external tool integrations."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        """Initialize the tool."""
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(tool=name)

    @abstractmethod
    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool with given data."""
        pass

    def log_execution(self, data: dict[str, Any]) -> None:
        """Log tool execution start."""
        self.logger.info(
            "Tool execution started", tool_name=self.name, data_keys=list(data.keys())
        )

    def log_completion(self, result: dict[str, Any]) -> None:
        """Log tool execution completion."""
        self.logger.info(
            "Tool execution completed",
            tool_name=self.name,
            result_keys=list(result.keys()),
        )

    def log_error(self, error: Exception, data: dict[str, Any]) -> None:
        """Log tool execution error."""
        self.logger.error(
            "Tool execution failed",
            tool_name=self.name,
            error=str(error),
            data_keys=list(data.keys()),
        )

    async def run(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run the tool with error handling."""
        try:
            self.log_execution(data)
            result = await self.execute(data)
            self.log_completion(result)
            return result
        except Exception as e:
            self.log_error(e, data)
            raise


class ToolRegistry:
    """Registry for managing tool instances."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self.tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.info("Tool registered", tool_name=tool.name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    async def execute_tool(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return await tool.run(data)


# Global tool registry instance
tool_registry = ToolRegistry()
