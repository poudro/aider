"""
Tools for integrating with the Aider coding assistant.
"""
import contextlib
import io
from typing import TYPE_CHECKING

from aider.commands import SwitchCoder

from .base import BaseTool, Tool, ToolError, register_tool

if TYPE_CHECKING:
    from aider.coders.base_coder import Coder


class AiderTools(BaseTool):
    """
    A class to hold the Aider coder instance for tools to use.
    This is not a tool itself, but a way to provide context to other tools.
    """

    coder: "Coder | None" = None

    @classmethod
    def set_coder(cls, coder: "Coder"):
        """Sets the Coder instance for all Aider tools to use."""
        cls.coder = coder


@register_tool
class AiderPromptTool(Tool):
    """A tool for sending a prompt to Aider."""

    name = "aider_prompt"
    description = "Send a prompt to the Aider coding assistant to modify the code."
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The prompt to send to Aider.",
            },
        },
        "required": ["prompt"],
    }

    def execute(self, prompt: str) -> str:
        if not AiderTools.coder:
            raise ToolError("Aider coder not available.")
        try:
            from aider.coders.base_coder import Coder

            agent_coder = AiderTools.coder

            # Create a new coder for editing, not another agent, to avoid recursion.
            # Use the main model's editor settings.
            editor_model = agent_coder.main_model.editor_model or agent_coder.main_model
            edit_format = (
                agent_coder.main_model.editor_edit_format or editor_model.edit_format
            )

            editor_coder = Coder.create(
                main_model=editor_model,
                edit_format=edit_format,
                io=agent_coder.io,
                from_coder=agent_coder,
                # Start with a clean history for this self-contained edit
                done_messages=[],
                cur_messages=[],
                # Don't let the editor-coder make commits on its own
                auto_commits=False,
                dirty_commits=False,
                # Pass along other relevant settings
                total_cost=agent_coder.total_cost,
                suggest_shell_commands=False,
            )

            result = editor_coder.run(with_message=prompt, preproc=False)

            # Sync back state to the main agent coder
            agent_coder.total_cost = editor_coder.total_cost
            agent_coder.aider_commit_hashes.update(editor_coder.aider_commit_hashes)
            if agent_coder.repo and agent_coder.repo.is_dirty():
                agent_coder.commands.cmd_commit(
                    f"Apply changes from agent prompt: {prompt[:50]}..."
                )

            return result or "Executed aider prompt and applied changes."
        except Exception as e:
            raise ToolError(f"An error occurred while running Aider prompt: {e}")


@register_tool
class AiderAddFileTool(Tool):
    """A tool for adding a file to the Aider chat context."""

    name = "aider_add_file"
    description = "Add a file to the Aider chat context for editing or reference."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to add.",
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        if not AiderTools.coder:
            raise ToolError("Aider coder not available.")
        try:
            AiderTools.coder.commands.cmd_add(path)
            return (
                f"Attempted to add '{path}' to Aider context. Use 'aider_get_context' to verify."
            )
        except Exception as e:
            raise ToolError(f"An error occurred while adding file '{path}': {e}")


@register_tool
class AiderDropFileTool(Tool):
    """A tool for dropping a file from the Aider chat context."""

    name = "aider_drop_file"
    description = "Remove a file from the Aider chat context."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to remove.",
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        if not AiderTools.coder:
            raise ToolError("Aider coder not available.")
        try:
            AiderTools.coder.commands.cmd_drop(path)
            return f"Attempted to remove '{path}' from Aider context. Use 'aider_get_context' to verify."
        except Exception as e:
            raise ToolError(f"An error occurred while removing file '{path}': {e}")


@register_tool
class AiderRunCommandTool(Tool):
    """A tool for running Aider commands."""

    name = "aider_run_command"
    description = (
        "Run an Aider command (e.g., /ls, /tokens). Excludes commands that are "
        "separate tools like /add, /drop, and prompts."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The Aider command to run, including the leading slash.",
            },
        },
        "required": ["command"],
    }

    def execute(self, command: str) -> str:
        if not AiderTools.coder:
            raise ToolError("Aider coder not available.")

        string_io = io.StringIO()
        original_io_print = AiderTools.coder.io.print
        original_io_tool_output = AiderTools.coder.io.tool_output
        original_io_tool_warning = AiderTools.coder.io.tool_warning
        original_io_tool_error = AiderTools.coder.io.tool_error

        try:
            AiderTools.coder.io.print = lambda msg="": string_io.write(msg + "\n")
            AiderTools.coder.io.tool_output = lambda msg, **kwargs: string_io.write(msg + "\n")
            AiderTools.coder.io.tool_warning = lambda msg, **kwargs: string_io.write(
                f"WARNING: {msg}\n"
            )
            AiderTools.coder.io.tool_error = lambda msg, **kwargs: string_io.write(
                f"ERROR: {msg}\n"
            )

            with contextlib.redirect_stdout(string_io):
                result = AiderTools.coder.commands.run(command)

            output = string_io.getvalue()
            if result:
                output += "\n" + str(result)

            return output.strip() if output.strip() else "Command executed."
        except SwitchCoder:
            raise ToolError(f"Command '{command}' is interactive and not supported in this tool.")
        except Exception as e:
            raise ToolError(f"An error occurred while running command '{command}': {e}")
        finally:
            AiderTools.coder.io.print = original_io_print
            AiderTools.coder.io.tool_output = original_io_tool_output
            AiderTools.coder.io.tool_warning = original_io_tool_warning
            AiderTools.coder.io.tool_error = original_io_tool_error


@register_tool
class AiderGetContextTool(Tool):
    """A tool for getting the current Aider chat context."""

    name = "aider_get_context"
    description = "Get the list of files currently in the Aider chat context."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self) -> str:
        if not AiderTools.coder:
            raise ToolError("Aider coder not available.")
        try:
            editable_files = AiderTools.coder.get_inchat_relative_files()
            read_only_files = [
                AiderTools.coder.get_rel_fname(f) for f in AiderTools.coder.abs_read_only_fnames
            ]

            context = "Editable files in chat:\n"
            if editable_files:
                context += "\n".join(f"- {f}" for f in sorted(editable_files))
            else:
                context += "None"

            context += "\n\nRead-only files in chat:\n"
            if read_only_files:
                context += "\n".join(f"- {f}" for f in sorted(read_only_files))
            else:
                context += "None"

            return context
        except Exception as e:
            raise ToolError(f"An error occurred while getting Aider context: {e}")
