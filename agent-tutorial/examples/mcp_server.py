"""Optional MCP SDK v2 example, not part of the standard-library exercise.
Requires mcp>=2,<3. Based on official v2 documentation; not integration-tested.
Run under an MCP host using stdio. Do not print to stdout.
"""
from mcp.server import MCPServer
from agent import BASE, Workspace, check_args, object_schema

mcp = MCPServer("Workspace Research")
workspace = Workspace(BASE / "workspace", allow_write=False)


@mcp.tool()
def read_workspace_note(path: str) -> dict:
    """Read bounded text from the fixed teaching workspace; no writes or network."""
    check_args(object_schema(path=True), {"path": path})
    return workspace.read({"path": path})


if __name__ == "__main__":
    mcp.run()  # SDK v2 default transport is stdio.
