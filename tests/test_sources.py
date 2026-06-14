"""Tests for the PulseLink source-ladder framework + backends (CONCEPT:PULSE-*).

HTTP is mocked; these are the unit + auth-gating tests. Live-network checks live in
``test_sources_live.py`` (marked ``live``, skipped by default).
"""

from __future__ import annotations

import pytest

from pulselink_mcp.sources import (
    CapabilityUnsupported,
    doctor,
    get_ladder,
    list_sources,
)
from pulselink_mcp.sources import base as base_mod
from pulselink_mcp.sources.base import (
    PulseDocument,
    PulseResult,
    SourceBackend,
    SourceLadder,
    set_credential_provider,
)
from pulselink_mcp.sources.dev import GitHubPublicBackend, GitHubTokenBackend
from pulselink_mcp.sources.forums import (
    HackerNewsBackend,
    RedditPublicBackend,
    V2exBackend,
)

# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #


class FakeMaterial:
    def __init__(self, headers=None, params=None, cookies=None):
        self.headers = headers or {}
        self.params = params or {}
        self.cookies = cookies or {}

    def merged_into(self, headers=None, params=None, cookies=None):
        h = dict(headers or {})
        h.update(self.headers)
        p = dict(params or {})
        p.update(self.params)
        c = dict(cookies or {})
        c.update(self.cookies)
        return h, p, c


class FakeCred:
    def __init__(self, material):
        self._m = material

    def materialize(self):
        return self._m


class FakeProvider:
    """Implements the provider contract the ladder relies on."""

    def __init__(self, creds: dict[str, FakeMaterial]):
        self._creds = creds

    def available(self, source: str) -> bool:
        return source in self._creds

    def get(self, source: str) -> FakeCred:
        return FakeCred(self._creds.get(source) or FakeMaterial())


class FakeResp:
    def __init__(self, json_data=None, text=""):
        self._json = json_data
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


@pytest.fixture
def captured_get(monkeypatch):
    """Patch ``requests.get`` in the sources base module; record calls."""
    calls = []

    def fake_get(url, params=None, headers=None, cookies=None, timeout=None):
        calls.append(
            {"url": url, "params": params, "headers": headers, "cookies": cookies}
        )
        return calls_resp["resp"]

    calls_resp = {"resp": FakeResp({})}
    monkeypatch.setattr(base_mod.requests, "get", fake_get)
    return calls, calls_resp


@pytest.fixture(autouse=True)
def _reset_provider():
    set_credential_provider(None)
    yield
    set_credential_provider(None)


# --------------------------------------------------------------------------- #
# Registry + doctor
# --------------------------------------------------------------------------- #


def test_registry_has_full_channel_parity():
    sources = set(list_sources())
    expected = {
        "youtube",
        "web",
        "rss",
        "news",
        "hackernews",
        "v2ex",
        "bilibili",
        "podcast",
        "github",
        "reddit",
        "x",
        "linkedin",
        "exa",
        "xiaohongshu",
        "xueqiu",
    }
    assert expected <= sources


def test_doctor_keyless_ready_auth_dark_without_creds():
    set_credential_provider(FakeProvider({}))  # no creds held
    health = doctor()
    yt = {h.backend: h for h in health["youtube"]}
    assert yt["yt-dlp"].ok and not yt["yt-dlp"].needs_auth
    x = {h.backend: h for h in health["x"]}
    assert all(not h.ok and h.needs_auth for h in x.values())  # no keyless X path
    reddit = {h.backend: h for h in health["reddit"]}
    assert reddit["reddit-public"].ok  # keyless fallback present
    assert reddit["reddit-oauth"].needs_auth


def test_doctor_auth_backend_lights_up_with_credential():
    set_credential_provider(FakeProvider({"x": FakeMaterial(headers={"a": "b"})}))
    health = {h.backend: h for h in doctor()["x"]}
    assert health["x-api"].ok and not health["x-api"].needs_auth


# --------------------------------------------------------------------------- #
# Backend parsing (mocked HTTP)
# --------------------------------------------------------------------------- #


def test_hackernews_search_parses_and_paginates(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp(
        {
            "hits": [
                {
                    "objectID": "1",
                    "title": "Rust is great",
                    "url": "http://x",
                    "author": "alice",
                    "points": 42,
                    "num_comments": 7,
                    "created_at": "2026-01-01",
                }
            ],
            "nbPages": 3,
        }
    )
    result = HackerNewsBackend().search("rust", cursor=None, limit=10)
    assert isinstance(result, PulseResult)
    assert result.documents[0].title == "Rust is great"
    assert result.documents[0].metrics["points"] == 42
    assert result.next_cursor == "1"  # page 0 of 3 → next is 1


def test_v2ex_list_parses(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp(
        [
            {
                "id": 9,
                "title": "Python tips",
                "url": "http://v2ex/9",
                "content": "body",
                "member": {"username": "bob"},
                "replies": 5,
                "node": {"name": "python"},
            }
        ]
    )
    result = V2exBackend().list_items("hot", None, 10)
    assert result.documents[0].author == "bob"
    assert result.documents[0].extra["node"] == "python"


def test_github_public_search_parses(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp(
        {
            "items": [
                {
                    "id": 5,
                    "full_name": "torvalds/linux",
                    "html_url": "http://gh",
                    "description": "kernel",
                    "owner": {"login": "torvalds"},
                    "stargazers_count": 100,
                    "language": "C",
                }
            ]
        }
    )
    result = GitHubPublicBackend().search("kernel", None, 10)
    assert result.documents[0].title == "torvalds/linux"
    assert result.documents[0].metrics["stars"] == 100


# --------------------------------------------------------------------------- #
# Auth application + ladder selection
# --------------------------------------------------------------------------- #


def test_auth_material_applied_to_request(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp({"items": []})
    set_credential_provider(
        FakeProvider({"github": FakeMaterial(headers={"Authorization": "token GH"})})
    )
    GitHubTokenBackend().search("x", None, 5)
    # The credential's header reached the outbound request.
    assert calls[-1]["headers"]["Authorization"] == "token GH"
    assert calls[-1]["headers"]["User-Agent"]  # default UA still present


def test_keyless_backend_sends_no_auth_header(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp({"items": []})
    set_credential_provider(
        FakeProvider({"github": FakeMaterial(headers={"Authorization": "token GH"})})
    )
    GitHubPublicBackend().search("x", None, 5)  # keyless variant
    assert "Authorization" not in calls[-1]["headers"]


def test_ladder_selects_auth_backend_when_credential_present(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp({"data": {"children": [], "after": None}})
    set_credential_provider(
        FakeProvider({"reddit": FakeMaterial(headers={"Authorization": "Bearer R"})})
    )
    get_ladder("reddit").search("python", None, 5)
    # The OAuth backend (higher in the ladder) ran → hit oauth.reddit.com.
    assert any("oauth.reddit.com" in c["url"] for c in calls)


def test_ladder_falls_back_to_keyless_without_credential(captured_get):
    calls, resp = captured_get
    resp["resp"] = FakeResp({"data": {"children": [], "after": None}})
    set_credential_provider(FakeProvider({}))  # no reddit credential
    get_ladder("reddit").search("python", None, 5)
    # Only the public (www) endpoint was hit; oauth backend was ineligible.
    assert all("oauth.reddit.com" not in c["url"] for c in calls)
    assert any("www.reddit.com" in c["url"] for c in calls)


def test_ladder_falls_through_on_backend_error():
    class Boom(SourceBackend):
        name = "boom"

        def search(self, query, cursor, limit):
            raise RuntimeError("upstream 500")

    class Works(SourceBackend):
        name = "works"

        def search(self, query, cursor, limit):
            return PulseResult(documents=[PulseDocument(id="ok")])

    ladder = SourceLadder("test", [Boom(), Works()])
    result = ladder.search("q", None, 5)
    assert result.documents[0].id == "ok"
    assert result.backend == "works"


def test_unsupported_capability_raises():
    class OnlySearch(SourceBackend):
        name = "s"

        def search(self, query, cursor, limit):
            return PulseResult()

    ladder = SourceLadder("test", [OnlySearch()])
    with pytest.raises(RuntimeError):
        ladder.fetch("x")  # no backend supports fetch → all-fail RuntimeError


def test_capability_unsupported_is_distinct_type():
    backend = RedditPublicBackend()
    with pytest.raises(CapabilityUnsupported):
        backend.transcribe("x")  # reddit has no transcribe


def test_unknown_source_raises_keyerror():
    with pytest.raises(KeyError):
        get_ladder("myspace")
