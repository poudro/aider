"""
Step executor for executing agent steps.
"""
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

from aider_agent.planner.task_planner import Plan, PlanStep
from aider_agent.tools.base import ToolError, get_tool

from .base import BaseExecutor

if TYPE_CHECKING:
    from aider.coders.base_coder import Coder
    from aider.io import InputOutput


logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Data class to hold the result of a single plan step execution."""

    step_id: int
    status: str  # 'success', 'failure', or 'skipped'
    output: Optional[str] = None
    error: Optional[str] = None


class StepExecutor(BaseExecutor):
    """
    The StepExecutor is responsible for executing the steps of a plan generated
    by the TaskPlanner. It handles tool selection, execution, error handling,
    retries, and user confirmations for critical steps.
    """

    def __init__(self, coder: "Coder", max_retries: int = 1):
        self.coder = coder
        self.io: "InputOutput" = coder.io
        self.max_retries = max_retries
        self.results: Dict[int, StepResult] = {}

    def execute_plan(self, plan: Plan) -> List[StepResult]:
        """
        Executes a plan by processing its steps in an order that respects
        their dependencies. Execution stops if a step fails.
        """
        self.results = {}
        steps_to_execute = plan.steps.copy()
        executed_steps = set()

        while len(executed_steps) < len(plan.steps):
            executable_steps = [
                step for step in steps_to_execute if self._dependencies_met(step)
            ]

            if not executable_steps:
                self.io.tool_error(
                    "Cannot proceed with plan. Check for circular or unmet dependencies."
                )
                # Mark remaining steps as skipped
                for step in steps_to_execute:
                    self.results[step.id] = StepResult(
                        step_id=step.id, status="skipped", error="Unmet dependencies"
                    )
                break

            for step in executable_steps:
                self.io.tool_output("-" * 20)
                self.io.tool_output(f"Executing Step {step.id}: [{step.type}] {step.description}")

                result = self._execute_step_with_retries(step)
                self.results[step.id] = result
                executed_steps.add(step.id)
                steps_to_execute.remove(step)

                if result.status != "success":
                    self.io.tool_error(
                        f"Step {step.id} failed: {result.error}. Aborting plan execution."
                    )
                    # Mark remaining steps as skipped
                    for remaining_step in steps_to_execute:
                        self.results[remaining_step.id] = StepResult(
                            step_id=remaining_step.id,
                            status="skipped",
                            error="Aborted due to previous step failure",
                        )
                    return list(self.results.values())

        self.io.tool_output("Plan execution completed.")
        return list(self.results.values())

    def _dependencies_met(self, step: PlanStep) -> bool:
        """Checks if all dependencies for a given step have been successfully met."""
        for dep_id in step.dependencies:
            if dep_id not in self.results or self.results[dep_id].status != "success":
                return False
        return True

    def _execute_step_with_retries(self, step: PlanStep) -> StepResult:
        """Executes a single step with retry logic."""
        retries = 0
        while True:
            try:
                return self._execute_step(step)
            except ToolError as e:
                error_message = f"Error in step {step.id}: {e}"
                logger.warning(error_message)

                if retries < self.max_retries:
                    retries += 1
                    self.io.tool_warning(
                        f"Step {step.id} failed. Retrying ({retries}/{self.max_retries})..."
                    )
                else:
                    self.io.tool_error(f"Step {step.id} failed after {self.max_retries} retries.")
                    return StepResult(step_id=step.id, status="failure", error=str(e))
            except Exception as e:
                error_message = f"An unexpected error occurred in step {step.id}: {e}"
                logger.error(error_message, exc_info=True)
                return StepResult(step_id=step.id, status="failure", error=str(e))

    def _execute_step(self, step: PlanStep) -> StepResult:
        """The core logic for executing a single step."""
        tool_name, params = self._get_tool_and_params(step)

        if not tool_name:
            return StepResult(
                step_id=step.id,
                status="failure",
                error=f"Could not determine tool for step type '{step.type}'.",
            )

        if self._is_critical_step(tool_name):
            subject = f"Step {step.id}: [{step.type.upper()}] {step.description}\n"
            subject += f"   - Tool: {tool_name}({params})"
            if not self.io.confirm_ask("Proceed with this step?", subject=subject, default="y"):
                return StepResult(step_id=step.id, status="skipped", output="User aborted step.")

        tool_class = get_tool(tool_name)
        tool_instance = tool_class()

        self.io.tool_output(f"Running tool '{tool_name}' with params: {params}")
        output = tool_instance.execute(**params)

        if output:
            self.io.tool_output(f"Tool '{tool_name}' output:\n{output}")

        return StepResult(step_id=step.id, status="success", output=output)

    def _get_tool_and_params(self, step: PlanStep) -> (Optional[str], Dict):
        """Determines the tool name and parameters for a given step."""
        if step.type == "coding":
            return "aider_prompt", {"prompt": step.description}
        elif step.type in ["research", "file_operation", "command"]:
            tool_name = step.details.get("tool")
            params = step.details.get("parameters", {})
            return tool_name, params
        return None, {}

    def _is_critical_step(self, tool_name: str) -> bool:
        """Determ-ines if a tool requires user confirmation before execution."""
        critical_tools = [
            "write_file",
            "delete_file",
            "create_directory",
            "aider_prompt",
            "aider_run_command",
        ]
        return tool_name in critical_tools
