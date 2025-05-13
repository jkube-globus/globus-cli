"""
A compatibility module for handling click v8.2.0+ and 8.1.x API differences.
"""

import importlib.metadata

CLICK_VERSION = importlib.metadata.version("click")

OLDER_CLICK_API = CLICK_VERSION.startswith("8.1.")
NEWER_CLICK_API = not OLDER_CLICK_API
