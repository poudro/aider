from aider_agent.config.settings import AgentSettings
from aider_agent.executor.step_executor import StepExecutor
from aider_agent.planner.task_planner import TaskPlanner
from aider_agent.tools.aider_tools import AiderTools
# Import tool modules to ensure they are registered via decorators
import aider_agent.tools.aider_tools  # noqa: F401
import aider_agent.tools.file_tools  # noqa: F401
import aider_agent.tools.web_tools  # noqa: F401

from .base_coder import Coder


class AgentCoder(Coder):
    """
    An agentic coder that uses a planner and tools to accomplish tasks.
    """

    edit_format = "agent"

    def __init__(self, main_model, io, **kwargs):
        super().__init__(main_model, io, **kwargs)
        self.agent_settings = AgentSettings.from_args(self.commands.args)
        self.planner = TaskPlanner(self)
        self.executor = StepExecutor(self, max_retries=self.agent_settings.max_retries)

        # Initialize tools
        AiderTools.set_coder(self)

    def run_one(self, user_message, preproc):
        self.init_before_message()

        if preproc:
            message = self.preproc_user_input(user_message)
            if not message:  # A command was run
                return
        else:
            message = user_message

        self.io.tool_output("Starting agent...")

        plan = self.planner.create_plan(message)
        if not plan:
            self.io.tool_error("Failed to create a plan. Aborting.")
            # Add a message to chat history to record failure
            summary = "Agent failed to create a plan."
            self.cur_messages += [
                dict(role="user", content=message),
                dict(role="assistant", content=summary),
            ]
            self.move_back_cur_messages(None)
            return

        # If --agent-auto-run-plan is not used, the plan is confirmed inside create_plan.
        results = self.executor.execute_plan(plan)

        # After execution, summarize the results
        success_steps = [r for r in results if r.status == "success"]
        failed_steps = [r for r in results if r.status == "failure"]
        skipped_steps = [r for r in results if r.status == "skipped"]

        summary = (
            f"Agent finished. {len(success_steps)} steps succeeded, {len(failed_steps)} failed,"
            f" {len(skipped_steps)} skipped."
        )

        self.io.tool_output(summary)

        if failed_steps:
            self.io.tool_error(f"Failed step: {failed_steps[0].step_id} - {failed_steps[0].error}")

        # This is an agent, so we don't have a final response to add to chat history in the same way.
        # We can add a summary of the agent's work.
        self.cur_messages += [
            dict(role="user", content=message),
            dict(role="assistant", content=summary),
        ]
        self.move_back_cur_messages(None)
