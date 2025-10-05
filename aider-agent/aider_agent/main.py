

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
