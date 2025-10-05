"""
Configuration settings for the Aider Agent.
"""
import argparse
from dataclasses import dataclass
from typing import List


@dataclass
class AgentSettings:
    """
    Settings for the Aider Agent, loaded from argparse.
    """

    # Models
    planner_model: str
    executor_model: str

    # Behavior
    max_retries: int
    max_plan_refinements: int
    auto_run_plan: bool

    # Tools
    enabled_tools: List[str]
    disabled_tools: List[str]

    # Permissions
    allow_shell: bool
    allow_file_operations: bool
    auto_approve_tool_use: bool

    # Cost Tracking
    max_total_cost: float
    warn_cost_per_message: float

    @classmethod
    def from_args(cls, args: argparse.Namespace):
        """
        Creates AgentSettings from an argparse.Namespace object.
        """
        return cls(
            planner_model=args.agent_planner_model,
            executor_model=args.agent_executor_model,
            max_retries=args.agent_max_retries,
            max_plan_refinements=args.agent_max_plan_refinements,
            auto_run_plan=args.agent_auto_run_plan,
            enabled_tools=args.agent_enabled_tools,
            disabled_tools=args.agent_disabled_tools,
            allow_shell=args.agent_allow_shell,
            allow_file_operations=args.agent_allow_file_operations,
            auto_approve_tool_use=args.agent_auto_approve_tool_use,
            max_total_cost=args.agent_max_total_cost,
            warn_cost_per_message=args.agent_warn_cost_per_message,
        )


