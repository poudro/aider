"""
Tools for file operations.
"""
import abc
import os
import shutil
from pathlib import Path

from .base import Tool, ToolError, register_tool


class BaseFileTool(Tool, abc.ABC):
    """Base class for file tools to provide a shared `resolve_path` method."""

    def resolve_path(self, path: str) -> Path:
        """
        Resolves a path to an absolute path, ensuring it's within the current working directory.
        This is a security measure to prevent tools from accessing files outside the project's scope.
        """
        # It's assumed that the agent runs with its CWD set to the project root.
        project_root = Path.cwd().resolve()
        absolute_path = (project_root / path).resolve()

        # Check if the resolved path is within the project root
        if project_root not in absolute_path.parents and absolute_path != project_root:
            raise ToolError(f"Path '{path}' is outside the project directory.")

        return absolute_path

    @abc.abstractmethod
    def execute(self, **kwargs) -> str:
        pass


@register_tool
class ReadFileTool(BaseFileTool):
    """A tool for reading the contents of a file."""

    name = "read_file"
    description = "Read the contents of a file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to read.",
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        try:
            resolved_path = self.resolve_path(path)
            if not resolved_path.is_file():
                raise ToolError(f"Path '{path}' is not a file.")
            with open(resolved_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            raise ToolError(f"File '{path}' not found.")
        except Exception as e:
            raise ToolError(f"An error occurred while reading file '{path}': {e}")


@register_tool
class WriteFileTool(BaseFileTool):
    """A tool for writing content to a file."""

    name = "write_file"
    description = (
        "Write content to a file. This will create the file if it doesn't exist and overwrite"
        " it if it does."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str, content: str) -> str:
        try:
            resolved_path = self.resolve_path(path)
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved_path, "w", encoding="utf-8") as file:
                file.write(content)
            return f"Successfully wrote to file '{path}'."
        except Exception as e:
            raise ToolError(f"An error occurred while writing to file '{path}': {e}")


@register_tool
class ListFilesTool(BaseFileTool):
    """A tool for listing files and directories."""

    name = "list_files"
    description = "List files and directories in a given path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "The path to the directory to list. Defaults to the current directory."
                ),
                "default": ".",
            },
        },
        "required": [],
    }

    def execute(self, path: str = ".") -> str:
        try:
            resolved_path = self.resolve_path(path)
            if not resolved_path.is_dir():
                raise ToolError(f"Path '{path}' is not a directory.")

            files = os.listdir(resolved_path)
            if not files:
                return f"Directory '{path}' is empty."
            return "\n".join(files)
        except FileNotFoundError:
            raise ToolError(f"Directory '{path}' not found.")
        except Exception as e:
            raise ToolError(f"An error occurred while listing files in '{path}': {e}")


@register_tool
class SearchFilesTool(BaseFileTool):
    """A tool for searching for a string within files."""

    name = "search_files"
    description = "Search for a string in files in a given directory."
    parameters = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The directory to search in. Defaults to the current directory.",
                "default": ".",
            },
            "query": {
                "type": "string",
                "description": "The string to search for.",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, directory: str = ".") -> str:
        try:
            resolved_dir = self.resolve_path(directory)
            if not resolved_dir.is_dir():
                raise ToolError(f"Path '{directory}' is not a directory.")

            matches = []
            for root, _, files in os.walk(resolved_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if query in line:
                                    relative_path = file_path.relative_to(Path.cwd())
                                    matches.append(f"{relative_path}:{i}:{line.strip()}")
                    except (IOError, OSError):
                        # Ignore files that can't be read
                        continue

            if not matches:
                return "No matches found."

            return "\n".join(matches)
        except Exception as e:
            raise ToolError(f"An error occurred while searching files: {e}")


@register_tool
class CreateDirectoryTool(BaseFileTool):
    """A tool for creating a new directory."""

    name = "create_directory"
    description = "Create a new directory."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the new directory to create.",
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        try:
            resolved_path = self.resolve_path(path)
            if resolved_path.exists():
                raise ToolError(f"Path '{path}' already exists.")
            resolved_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created directory '{path}'."
        except Exception as e:
            raise ToolError(f"An error occurred while creating directory '{path}': {e}")


@register_tool
class DeleteFileTool(BaseFileTool):
    """A tool for deleting a file or directory."""

    name = "delete_file"
    description = (
        "Delete a file or a directory. To delete a non-empty directory, `recursive` must be set"
        " to `true`."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the file or directory to delete.",
            },
            "recursive": {
                "type": "boolean",
                "description": (
                    "If true, allows recursive deletion of directories. Defaults to false."
                ),
                "default": False,
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str, recursive: bool = False) -> str:
        try:
            resolved_path = self.resolve_path(path)
            if not resolved_path.exists():
                raise ToolError(f"Path '{path}' not found.")

            if resolved_path.is_file():
                resolved_path.unlink()
                return f"Successfully deleted file '{path}'."
            elif resolved_path.is_dir():
                if recursive:
                    shutil.rmtree(resolved_path)
                    return f"Successfully deleted directory '{path}' recursively."
                else:
                    if any(resolved_path.iterdir()):
                        raise ToolError(
                            f"Directory '{path}' is not empty. Use recursive=True to delete."
                        )
                    resolved_path.rmdir()
                    return f"Successfully deleted empty directory '{path}'."
            else:
                raise ToolError(f"Path '{path}' is not a file or directory.")
        except Exception as e:
            raise ToolError(f"An error occurred while deleting '{path}': {e}")
