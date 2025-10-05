"""
Main task planner.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

from aider.exceptions import LiteLLMExceptions

from ..prompts.agent_prompts import AgentPrompts
from ..tools.base import get_all_tools
from .base import BasePlanner

if TYPE_CHECKING:
    from aider.coders.base_coder import Coder
    from aider.io import InputOutput


logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    id: int
    type: str  # e.g., 'coding', 'research', 'file_operation', 'command'
    description: str
    dependencies: List[int] = field(default_factory=list)
    details: Dict = field(default_factory=dict)  # For type-specific info like tool name and params


@dataclass
class Plan:
    steps: List[PlanStep] = field(default_factory=list)


class TaskPlanner(BasePlanner):
    """
    A planner that breaks down complex user requests into actionable steps,
    integrates with an LLM to create plans, validates steps, and supports
    plan refinement through user confirmation.
    """

    def __init__(self, coder: "Coder"):
        self.coder = coder
        self.io: "InputOutput" = coder.io
        self.prompts = AgentPrompts()

    def create_plan(self, user_request: str) -> Optional[Plan]:
        """
        Creates a plan to address the user's request.

        This involves:
        1. Formatting a prompt for the LLM with the user request and available tools.
        2. Calling the LLM to generate a plan.
        3. Parsing and validating the plan.
        4. Asking for user confirmation to proceed with the plan.
        """
        self.io.tool_output("Creating a plan to address your request...")

        tools = get_all_tools()
        tools_json_schema = json.dumps([tool.get_schema() for tool in tools.values()], indent=2)

        prompt = self.prompts.plan_creation_prompt.format(
            tools_json_schema=tools_json_schema,
            user_request=user_request,
        )

        messages = [{"role": "user", "content": prompt}]

        try:
            # We need a non-streaming response to get the full JSON plan.
            _hash, response = self.coder.main_model.send_completion(messages, None, stream=False)
            if not response.choices or not response.choices[0].message.content:
                self.io.tool_error("Received an empty plan from the LLM.")
                return None
            plan_json_str = response.choices[0].message.content
        except LiteLLMExceptions().exceptions_tuple() as e:
            self.io.tool_error(f"Error creating plan: {e}")
            return None

        try:
            # The LLM sometimes returns a JSON object wrapped in ```json ... ```
            if plan_json_str.strip().startswith("```json"):
                plan_json_str = plan_json_str.strip()[7:-3].strip()

            plan_data = json.loads(plan_json_str)
            plan = self._parse_plan(plan_data)
        except (json.JSONDecodeError, TypeError) as e:
            self.io.tool_error(f"Failed to parse plan from LLM: {e}")
            self.io.tool_output(f"LLM response:\n{plan_json_str}")
            return None

        if not self._validate_plan(plan):
            self.io.tool_error("Plan validation failed.")
            # TODO: Add refinement loop
            return None

        self.io.tool_output("Generated plan:")
        self.io.tool_output(self.format_plan(plan))

        if self.io.confirm_ask("Do you want to proceed with this plan?"):
            return plan
        else:
            self.io.tool_output("Plan aborted by user.")
            return None

    def _parse_plan(self, plan_data: Dict) -> Plan:
        steps = [PlanStep(**step_data) for step_data in plan_data.get("steps", [])]
        return Plan(steps=steps)

    def _validate_plan(self, plan: Plan) -> bool:
        step_ids = {step.id for step in plan.steps}
        if len(step_ids) != len(plan.steps):
            self.io.tool_error("Plan contains duplicate step IDs.")
            return False

        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    self.io.tool_error(f"Step {step.id} has an invalid dependency: {dep_id}")
                    return False
        # TODO: Add circular dependency check
        return True

    def format_plan(self, plan: Plan) -> str:
        formatted_plan = "Execution Plan:\n"
        for i, step in enumerate(plan.steps):
            formatted_plan += f"{i + 1}. (ID: {step.id}) [{step.type.upper()}] {step.description}\n"
            if step.dependencies:
                formatted_plan += f"   - Depends on: {sorted(step.dependencies)}\n"
            if step.details and step.details.get("tool"):
                tool = step.details["tool"]
                params = step.details.get("parameters", {})
                formatted_plan += f"   - Tool: {tool}({json.dumps(params)})\n"
        return formatted_plan
