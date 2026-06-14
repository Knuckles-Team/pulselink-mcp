#!/usr/bin/python
"""Facade re-export of the modular api/ sub-package (backward compatibility)."""

from .api import *  # noqa: F401,F403
from .api import __all__ as _api_all

__all__ = list(_api_all)
