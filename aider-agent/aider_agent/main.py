import argparse

def get_agent_parser(agent_default_config_files, git_root):
    """Create and configure the argument parser for the aider-agent."""
    parser = argparse.ArgumentParser(
        description="aider-agent: An AI-powered coding agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars="@",
        add_help=False,
    )

    agent_group = parser.add_argument_group("Agent Settings")

    # Model configuration
    agent_group.add_argument(
        "--agent-model",
        type=str,
        default=None,
        metavar="MODEL",
        help=(
            "Model to use for the agent. Defaults to --model if not set. Used for both planner and"
            " executor unless overridden."
        ),
    )
    agent_group.add_argument(
        "--agent-planner-model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Model to use for planning. Overrides --agent-model.",
    )
    agent_group.add_argument(
        "--agent-executor-model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Model to use for code generation and execution tasks. Overrides --agent-model.",
    )

    # Behavior settings
    agent_group.add_argument(
        "--agent-max-retries",
        type=int,
        default=1,
        help="Maximum number of retries for a failed step.",
    )
    agent_group.add_argument(
        "--agent-max-plan-refinements",
        type=int,
        default=3,
        help="Maximum number of times to refine the plan.",
    )
    agent_group.add_argument(
        "--agent-auto-run-plan",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Automatically run the plan without user confirmation (default: False).",
    )

    # Tool settings
    agent_group.add_argument(
        "--agent-enabled-tools",
        type=str,
        nargs="+",
        default=["*"],
        help="List of enabled tools. '*' means all tools.",
    )
    agent_group.add_argument(
        "--agent-disabled-tools",
        type=str,
        nargs="+",
        default=[],
        help="List of disabled tools.",
    )

    # Security and permission settings
    agent_group.add_argument(
        "--agent-allow-shell",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow the agent to run shell commands (default: False).",
    )
    agent_group.add_argument(
        "--agent-allow-file-operations",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Allow the agent to perform file operations (default: True).",
    )
    agent_group.add_argument(
        "--agent-auto-approve-tool-use",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Automatically approve the use of critical tools (default: False).",
    )

    # Cost tracking settings
    agent_group.add_argument(
        "--agent-max-total-cost",
        type=float,
        default=0.50,
        help="Maximum total cost in USD for the agent session.",
    )
    agent_group.add_argument(
        "--agent-warn-cost-per-message",
        type=float,
        default=0.10,
        help="Warn when a single message costs more than this amount in USD.",
    )

    return parser


def parse_agent_args(
    git_root,
    args,
    unknown,
    generate_search_path_list=None,
    get_agent_parser=None,
):
    """
    Parse arguments specific to the aider-agent.
    """
    agent_default_config_files = generate_search_path_list(
        ".aider-agent.conf.yml", git_root, None
    )
    agent_parser = get_agent_parser(agent_default_config_files, git_root)
    args, unknown = agent_parser.parse_known_args(unknown, namespace=args)

    if not args.agent_model:
        args.agent_model = args.model
    if not args.agent_planner_model:
        args.agent_planner_model = args.agent_model
    if not args.agent_executor_model:
        args.agent_executor_model = args.agent_model

    return args, unknown


def create_agent_models(args):
    """
    Create and return agent model instances.
    
    Args:
        args: Parsed arguments containing agent model settings
        
    Returns:
        tuple: (agent_model, agent_planner_model, agent_executor_model)
    """
    from aider import models
    
    agent_model = models.Model(
        args.agent_model,
        verbose=args.verbose,
    )
    agent_planner_model = models.Model(
        args.agent_planner_model,
        verbose=args.verbose,
    )
    agent_executor_model = models.Model(
        args.agent_executor_model,
        verbose=args.verbose,
    )
    
    return agent_model, agent_planner_model, agent_executor_model
