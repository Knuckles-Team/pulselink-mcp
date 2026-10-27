"""Keep docs pushes separate from guarded package publication."""

from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def _push_matches(workflow, ref):
    # PyYAML's YAML 1.1 reader represents the Actions "on" key as True.
    push = workflow[True]["push"]
    kind, name = ref.removeprefix("refs/").split("/", 1)
    filters = push.get({"heads": "branches", "tags": "tags"}[kind], [])
    return any(fnmatchcase(name, pattern) for pattern in filters)


@pytest.mark.parametrize(
    "ref, expected",
    [
        ("refs/heads/main", True),
        ("refs/heads/docs-update", False),
        ("refs/tags/v2.1.0", False),
    ],
)
def test_only_main_starts_package_publication(ref, expected):
    assert _push_matches(_workflow("pipeline.yml"), ref) is expected


def test_each_package_publisher_uses_the_shared_pipelines():
    jobs = _workflow("pipeline.yml")["jobs"]
    assert set(jobs) == {"publish-pypi"}
    assert jobs["publish-pypi"]["uses"].endswith("/python_pipeline.yml@main")
    assert _workflow("pipeline.yml")[True]["push"]["paths-ignore"] == [
        "docker/Dockerfile",
        ".github/workflows/container-release.yml",
        ".bumpversion.cfg",
        "specs/**/status.json",
    ]
    container = _workflow("container-release.yml")
    assert container[True]["push"] == {
        "branches": ["main"],
        "paths": ["docker/Dockerfile"],
    }
    assert container["jobs"]["publish-docker"]["needs"] == "verify-public-wheel"
    assert container["jobs"]["publish-docker"]["uses"].endswith(
        "/container_pipeline.yml@main"
    )
    assert container["jobs"]["publish-docker"]["with"] == {
        "legacy_profile": True,
        "render_connector": False,
    }
    for publisher in (jobs["publish-pypi"], container["jobs"]["publish-docker"]):
        assert "if" not in publisher
        assert not publisher.get("continue-on-error", False)
    guard = container["jobs"]["verify-public-wheel"]["steps"][-1]
    assert guard["with"] == {
        "mode": "published-wheel",
        "distribution": "pulselink-mcp",
        "module": "pulselink_mcp",
        "legacy-profile": True,
    }


def test_pages_publishes_the_spec_dashboard_on_spec_changes():
    workflow = _workflow("pages.yml")
    publisher = workflow["jobs"]["publish-pages"]

    assert not (ROOT / ".github/workflows/docs.yml").exists()
    assert publisher["uses"] == (
        "Knuckles-Team/pipelines/.github/workflows/pages_pipeline.yml@main"
    )
    assert publisher["with"] == {
        "content_source": "docs",
        "spec_dashboard_enabled": True,
        "spec_dashboard_config": ".github/spec-dashboard.json",
    }
    assert workflow[True]["push"]["paths"] == [
        "docs/**",
        "mkdocs.yml",
        "README.md",
        "specs/**",
        ".github/spec-dashboard.json",
        ".github/workflows/pages.yml",
    ]
    assert (ROOT / ".github/spec-dashboard.json").read_text() == (
        '{\n  "version": 1,\n  "sources": [\n'
        '    {\n      "glob": "specs/*/status.json",\n'
        '      "kind": "spec"\n    }\n  ]\n}\n'
    )


@pytest.mark.parametrize(
    "path, expected",
    [
        ("docker/Dockerfile", False),
        (".github/workflows/container-release.yml", False),
        (".bumpversion.cfg", False),
        ("specs/sdk/status.json", False),
        ("pulselink_mcp/specs/openapi.json", True),
        ("pyproject.toml", True),
        ("uv.lock", True),
        ("pulselink_mcp/mcp_server.py", True),
        ("README.md", True),
        (".github/workflows/pipeline.yml", True),
    ],
)
def test_package_publication_skips_only_container_pin_refresh(path, expected):
    ignores = _workflow("pipeline.yml")[True]["push"]["paths-ignore"]
    assert (not any(fnmatchcase(path, pattern) for pattern in ignores)) is expected


@pytest.mark.parametrize(
    "paths, expected",
    [
        (["docker/Dockerfile", ".github/workflows/container-release.yml"], False),
        ([".github/workflows/container-release.yml", "pulselink_mcp/mcp_server.py"], True),
        ([".github/workflows/container-release.yml", "pyproject.toml"], True),
    ],
)
def test_mixed_changes_keep_source_and_version_publication(paths, expected):
    ignores = _workflow("pipeline.yml")[True]["push"]["paths-ignore"]
    assert any(
        not any(fnmatchcase(path, pattern) for pattern in ignores) for path in paths
    ) is expected
