"""
Base classes for tools.
"""
import abc
import json
import logging
from typing import ClassVar, Dict, Type


class BaseTool:
    """Base class for all tools."""

    pass


# Set up logging
logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Custom exception for tool-related errors."""

    pass


_tool_registry: Dict[str, Type["Tool"]] = {}


def register_tool(tool_class: Type["Tool"]):
    """Registers a tool in the global tool registry."""
    if not issubclass(tool_class, Tool):
        raise TypeError("Registered tool must be a subclass of Tool.")

    name = tool_class.name
    if name in _tool_registry:
        logger.warning(f"Tool '{name}' is already registered. Overwriting.")

    _tool_registry[name] = tool_class
    return tool_class


def get_tool(name: str) -> Type["Tool"]:
    """Retrieves a tool from the registry by name."""
    if name not in _tool_registry:
        raise ToolError(f"Tool '{name}' not found in registry.")
    return _tool_registry[name]


def get_all_tools() -> Dict[str, Type["Tool"]]:
    """Returns a dictionary of all registered tools."""
    return _tool_registry.copy()


class Tool(BaseTool, abc.ABC):
    """Abstract base class for all tools."""

    name: ClassVar[str]
    description: ClassVar[str]
    parameters: ClassVar[Dict] = {}

    @abc.abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Executes the tool with the given parameters.

        Args:
            **kwargs: The parameters for the tool, matching the 'parameters' schema.

        Returns:
            A string representation of the tool's output.
        """
        pass

    def __call__(self, **kwargs) -> str:
        """
        Calls the tool's execute method with error handling and logging.
        """
        logger.info(f"Executing tool '{self.name}' with parameters: {kwargs}")
        try:
            # Here one might add parameter validation against self.parameters schema
            result = self.execute(**kwargs)
            logger.info(f"Tool '{self.name}' executed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{self.name}': {e}", exc_info=True)
            raise ToolError(f"An error occurred while executing {self.name}: {e}")

    @classmethod
    def get_schema(cls) -> Dict:
        """Returns the tool's schema for use with function-calling LLMs."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.parameters,
        }
