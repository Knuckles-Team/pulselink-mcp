from pulselink_mcp.mcp_server import get_mcp_instance


def test_mcp_instance_registration(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pulselink-mcp"])
    mcp, args, middlewares = get_mcp_instance()
    assert mcp is not None
