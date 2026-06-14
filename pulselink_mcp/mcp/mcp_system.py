import json

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client


def register_system_tools(mcp: FastMCP):
    """Register system tag dynamic tools."""

    @mcp.tool(tags={"system"})
    async def system_operations(
        action: str = Field(
            description="Action to perform. Must be 'status' or 'info'."
        ),
        params_json: str = Field(
            default="{}", description="JSON string of parameters to pass to the action."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Manage system tag operations. CONCEPT:PULSE-001"""
        if ctx:
            ctx.info("Executing system tool...")
        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        if action == "status":
            try:
                return client.get_system_status(**kwargs)
            except Exception as e:
                return {"error": str(e)}
        return {"info": "System operations dynamic placeholder."}
