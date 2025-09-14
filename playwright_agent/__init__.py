"""
Playwright Agent - An intelligent web scraping agent built with AutoGen and OpenRouter AI

This package provides a web scraping agent that automatically determines the best
approach for extracting data from web pages using the Playwright MCP server
and AI-powered analysis through OpenRouter.
"""

__version__ = "0.1.0"

from .agent import PlaywrightAgent
from .models import (
    ScrapingRequest, 
    ScrapingResult, 
    ExtractionPoint, 
    PageAnalysis, 
    SelectorCandidate,
    OpenRouterConfig
)
from .openrouter_client import OpenRouterClient

__all__ = [
    "PlaywrightAgent", 
    "ScrapingRequest", 
    "ScrapingResult", 
    "ExtractionPoint",
    "PageAnalysis",
    "SelectorCandidate", 
    "OpenRouterConfig",
    "OpenRouterClient"
]