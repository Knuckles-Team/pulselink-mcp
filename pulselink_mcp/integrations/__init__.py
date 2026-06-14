"""PulseLink integrations — optional capabilities other packages import lazily.

CONCEPT:PULSE-006 — X search/browse tools (xAI/Grok index), externalized from
agent-utilities so its core carries no X integration. agent-utilities imports
``x_tools`` from here optionally (try/except ImportError).
"""

from .x_search_tool import browse_x_post, x_search, x_tools

__all__ = ["x_tools", "x_search", "browse_x_post"]
