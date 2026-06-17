#!/usr/bin/python
import logging
import os
import sys
import warnings

__version__ = "0.2.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def agent_server():
    from agent_utilities import (
        build_system_prompt_from_workspace,
        create_agent_parser,
        create_agent_server,
        initialize_workspace,
        load_identity,
    )

    warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastmcp")

    initialize_workspace()
    meta = load_identity()
    agent_name = os.getenv("DEFAULT_AGENT_NAME", meta.get("name", "PulseLink MCP"))

    print(f"{agent_name} v{__version__}", file=sys.stderr)
    parser = create_agent_parser()
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    create_agent_server(
        mcp_url=args.mcp_url,
        mcp_config=args.mcp_config or "mcp_config.json",
        host=args.host,
        port=args.port,
        provider=args.provider,
        model_id=args.model_id,
        router_model=args.model_id,
        agent_model=args.model_id,
        base_url=args.base_url,
        api_key=args.api_key,
        agent_description=os.getenv(
            "AGENT_DESCRIPTION",
            meta.get(
                "description",
                "PulseLink — keyless open-web & social research source (MCP Server + A2A Server)",
            ),
        ),
        system_prompt=os.getenv(
            "AGENT_SYSTEM_PROMPT",
            meta.get("content") or build_system_prompt_from_workspace(),
        ),
        custom_skills_directory=args.custom_skills_directory,
        enable_web_ui=args.web,
        enable_otel=args.otel,
        otel_endpoint=args.otel_endpoint,
        otel_headers=args.otel_headers,
        otel_public_key=args.otel_public_key,
        otel_secret_key=args.otel_secret_key,
        otel_protocol=args.otel_protocol,
        debug=args.debug,
    )


if __name__ == "__main__":
    agent_server()
