import importlib


def test_mcp_server_module_importable():
    assert importlib.import_module("pulselink_mcp.mcp_server") is not None
