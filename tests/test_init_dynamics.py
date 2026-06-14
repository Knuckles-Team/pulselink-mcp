import importlib


def test_package_imports():
    module = importlib.import_module("pulselink_mcp")
    assert hasattr(module, "__all__")
