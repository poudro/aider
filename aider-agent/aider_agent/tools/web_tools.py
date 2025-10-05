"""
Tools for web operations such as searching, scraping, and fetching content.
"""
import logging
from typing import List

from aider.scrape import Scraper

from .aider_tools import AiderTools
from .base import Tool, ToolError, register_tool

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logger = logging.getLogger(__name__)


def _get_scraper() -> Scraper:
    """Helper function to instantiate the aider Scraper."""
    # This makes assumptions about Scraper's constructor based on its usage in aider's commands.
    # It avoids playwright by default to reduce overhead, as many scraping tasks don't need it.
    verify_ssl = True
    if AiderTools.coder:
        verify_ssl = AiderTools.coder.commands.verify_ssl
    return Scraper(print_error=logger.error, playwright_available=False, verify_ssl=verify_ssl)


@register_tool
class WebSearchTool(Tool):
    """A tool for performing web searches."""

    name = "web_search"
    description = "Search the web for a given query."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "max_results": {
                "type": "integer",
                "description": "The maximum number of search results to return.",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, max_results: int = 5) -> str:
        if DDGS is None:
            raise ToolError(
                "The `duckduckgo-search` package is not installed. Please install it with `pip"
                " install duckduckgo-search`."
            )
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No search results found."

            formatted_results = []
            for r in results:
                formatted_results.append(
                    f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n"
                )
            return "\n".join(formatted_results)
        except Exception as e:
            raise ToolError(f"An error occurred during the web search: {e}")


@register_tool
class WebScrapeTool(Tool):
    """A tool for scraping the content of a web page."""

    name = "web_scrape"
    description = "Scrape and return the cleaned (markdown) content of a web page."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the web page to scrape.",
            },
        },
        "required": ["url"],
    }

    def execute(self, url: str) -> str:
        try:
            scraper = _get_scraper()
            content = scraper.scrape(url)
            if not content:
                raise ToolError("Failed to scrape content from the URL.")
            return content
        except Exception as e:
            raise ToolError(f"An error occurred while scraping the URL '{url}': {e}")


@register_tool
class WebFetchTool(Tool):
    """A tool for fetching the raw content of a web page."""

    name = "web_fetch"
    description = "Fetch and return the raw HTML content of a web page."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the web page to fetch.",
            },
        },
        "required": ["url"],
    }

    def execute(self, url: str) -> str:
        try:
            scraper = _get_scraper()
            content = scraper.fetch_raw(url)
            if content is None:
                raise ToolError("Failed to fetch content from the URL.")
            return content
        except Exception as e:
            raise ToolError(f"An error occurred while fetching the URL '{url}': {e}")
