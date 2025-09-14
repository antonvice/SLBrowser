"""
SLBrowser - AI-Powered Terminal Web Browser for Content Analysis and Research.

A modern, intelligent terminal-based web browser that combines web scraping,
AI-powered content analysis, and beautiful terminal formatting to provide
an efficient research and content exploration experience.

Key Components:
- models: Pydantic data models for structured content
- ai: Pydantic AI integration with Google Gemini
- web: Async web scraping and content extraction
- search: DuckDuckGo web search functionality
- tui: Rich-powered terminal interface
"""

from __future__ import annotations

__version__ = "0.1.2"
__author__ = "Anton Vice <anton@selflayer.com>"
__description__ = "AI-powered terminal web browser for content analysis and research"


# Core exceptions
class SLBrowserError(Exception):
    """Base exception for SLBrowser application."""

    pass


class APIError(SLBrowserError):
    """Raised when API operations fail."""

    pass


class WebError(SLBrowserError):
    """Raised when web operations fail."""

    pass


class SearchError(SLBrowserError):
    """Raised when search operations fail."""

    pass


# Package-level exports
__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "SLBrowserError",
    "APIError",
    "WebError",
    "SearchError",
]
