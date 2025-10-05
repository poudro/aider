# Aider Agent Mode

Aider's Agent Mode is an experimental feature that enables an AI agent to tackle complex software development tasks by creating and executing a plan. The agent can use various tools to interact with your codebase, search the web, and perform other actions to fulfill your request.

## Overview

When you use Aider in agent mode, you provide a high-level goal. The agent then:

1.  **Creates a Plan**: The agent analyzes your request and breaks it down into a series of steps. This plan outlines the actions the agent will take, such as reading files, searching for information, or modifying code.
2.  **User Approval**: Before executing the plan, the agent presents it to you for approval. You can review the steps and decide whether to proceed.
3.  **Executes the Plan**: Once you approve, the agent executes the plan step-by-step, using its available tools. It will show you its progress and the results of each step.
4.  **Handles Errors**: If a step fails, the agent can analyze the error and either retry the step, refine the plan, or ask you for guidance.
5.  **Summarizes Work**: After completing the plan, the agent provides a summary of the work done.

## Installation

Agent mode is included with Aider. However, some tools may require additional packages. For example, the `web_search` tool uses `duckduckgo-search`. To enable it, install the extra dependency:

```bash
pip install "aider-chat[agent]"
```
or
```bash
pip install duckduckgo-search
```

## Usage Examples

You can start agent mode from the Aider chat prompt or with a command-line argument.

### Interactive Mode

To switch to agent mode within an Aider chat session, use the `/agent` command:

```
/agent
```

You can then provide your high-level request.

Alternatively, you can provide the request directly with the command:

```
/agent Refactor the authentication logic to use a more secure hashing algorithm.
```

### Command-Line

You can start Aider directly in agent mode with a prompt using the `--message` (or `-m`) flag combined with `--edit-format agent`:

```bash
aider --edit-format agent -m "Add a new endpoint to the API for user profile updates."
```

## Configuration

You can configure the agent's behavior using command-line arguments or by adding them to your `.aider.conf.yml` file.

### Command-Line Arguments

Here are the available agent-specific settings:

-   `--agent-planner-model <MODEL>`: Model to use for planning.
-   `--agent-executor-model <MODEL>`: Model to use for code generation and execution tasks.
-   `--agent-max-retries <NUM>`: Maximum number of retries for a failed step (default: 1).
-   `--agent-max-plan-refinements <NUM>`: Maximum number of times to refine the plan (default: 3).
-   `--agent-auto-run-plan`: Automatically run the plan without user confirmation (default: False).
-   `--agent-enabled-tools <TOOL1> <TOOL2> ...`: List of enabled tools. '*' means all tools (default: '*').
-   `--agent-disabled-tools <TOOL1> <TOOL2> ...`: List of disabled tools.
-   `--agent-allow-shell`: Allow the agent to run shell commands (default: False).
-   `--agent-allow-file-operations`: Allow the agent to perform file operations (default: True).
-   `--agent-auto-approve-tool-use`: Automatically approve the use of critical tools (default: False).
-   `--agent-max-total-cost <USD>`: Maximum total cost in USD for the agent session (default: 0.50).
-   `--agent-warn-cost-per-message <USD>`: Warn when a single message costs more than this amount in USD (default: 0.10).

### Example `.aider.conf.yml`

Here is an example of how to configure the agent in your `.aider.conf.yml` file:

```yaml
# Use agent mode by default
edit-format: agent

# Agent-specific settings
agent-planner-model: gpt-4o
agent-executor-model: gpt-4o
agent-max-retries: 2
agent-allow-shell: true
agent-auto-run-plan: false
agent-max-total-cost: 1.00
agent-disabled-tools:
  - delete_file
```

## Tools

The agent has access to a variety of tools to help it complete tasks.

### Aider Tools

These tools integrate with Aider's core functionality.

-   `aider_prompt`: Sends a prompt to the Aider coding assistant to modify code. This is the primary tool for code changes.
-   `aider_add_file`: Adds a file to the Aider chat context for editing or reference.
-   `aider_drop_file`: Removes a file from the Aider chat context.
-   `aider_run_command`: Runs an Aider command (e.g., `/ls`, `/tokens`).
-   `aider_get_context`: Gets the list of files currently in the Aider chat context.

### File Tools

These tools allow the agent to interact with the file system.

-   `read_file`: Reads the contents of a file.
-   `write_file`: Writes content to a file, creating it if it doesn't exist or overwriting it if it does.
-   `list_files`: Lists files and directories in a given path.
-   `search_files`: Searches for a string within files in a directory.
-   `create_directory`: Creates a new directory.
-   `delete_file`: Deletes a file or directory.

### Web Tools

These tools allow the agent to access information from the internet.

-   `web_search`: Performs a web search using DuckDuckGo.
-   `web_scrape`: Scrapes the cleaned (markdown) content of a web page.
-   `web_fetch`: Fetches the raw HTML content of a web page.

## Troubleshooting

-   **Plan Generation Fails**: If the agent fails to create a plan, try rephrasing your request to be more specific. You can also try using a more powerful model for the planner (`--agent-planner-model`).
-   **Tool Errors**: If a tool fails repeatedly, there might be an issue with the tool's parameters or the environment. Check the error messages for clues. You can also try to perform the action manually to see if it works.
-   **Security**: Be cautious when enabling shell access (`--agent-allow-shell`) or auto-approval (`--agent-auto-run-plan`, `--agent-auto-approve-tool-use`), as the agent could perform destructive actions. Always review the plan carefully before approving it.
