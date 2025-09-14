"""
Data models for the Playwright Agent
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionPoint(BaseModel):
    """Defines a specific data point to extract from a webpage"""
    name: str = Field(description="Unique identifier for this data point")
    type: Literal["text", "number", "url", "image", "list"] = Field(description="Type of data to extract")
    description: str = Field(description="Human-readable description of what to extract")
    selector: Optional[str] = Field(default=None, description="CSS selector (auto-discovered if not provided)")
    required: bool = Field(default=True, description="Whether this field is required")


class OpenRouterConfig(BaseModel):
    """Configuration for OpenRouter AI integration"""
    api_key: Optional[str] = Field(default=None, description="OpenRouter API key (defaults to OPENROUTER_API_KEY env var)")
    model: str = Field(default="anthropic/claude-3.5-sonnet", description="Model to use for AI analysis")
    enabled: bool = Field(default=True, description="Enable AI-powered analysis")
    max_tokens: int = Field(default=1000, description="Maximum tokens for AI responses")
    temperature: float = Field(default=0.3, description="Temperature for AI generation")


class ScrapingRequest(BaseModel):
    """Request configuration for web scraping"""
    url: str = Field(description="URL to scrape")
    extraction_points: List[ExtractionPoint] = Field(description="List of data points to extract")
    max_iterations: int = Field(default=5, description="Maximum number of iterations for improvement")
    output_file: str = Field(default="scraper_script.py", description="Output file for generated script")
    method: Optional[Literal["auto", "http", "browser"]] = Field(
        default="auto", 
        description="Scraping method: auto (agent decides), http (requests), browser (selenium/playwright)"
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    wait_for_load: bool = Field(default=True, description="Wait for page to fully load")
    openrouter_config: Optional[OpenRouterConfig] = Field(default=None, description="OpenRouter AI configuration")


class ScrapingResult(BaseModel):
    """Result of a scraping operation"""
    success: bool = Field(description="Whether the scraping was successful")
    data: Dict[str, Any] = Field(description="Extracted data")
    script_path: str = Field(description="Path to the generated script")
    method_used: str = Field(description="Scraping method that was used")
    iterations: int = Field(description="Number of iterations needed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    selectors_found: Dict[str, str] = Field(description="CSS selectors that were discovered/used")


class PageAnalysis(BaseModel):
    """Analysis of a webpage structure"""
    title: str = Field(description="Page title")
    has_javascript: bool = Field(description="Whether page uses JavaScript")
    load_time: float = Field(description="Page load time in seconds")
    element_count: int = Field(description="Total number of elements on page")
    suggested_method: Literal["http", "browser"] = Field(description="Recommended scraping method")
    confidence: float = Field(description="Confidence in method recommendation (0-1)")
    reason: str = Field(description="Explanation for method choice")


class SelectorCandidate(BaseModel):
    """A candidate CSS selector for an extraction point"""
    selector: str = Field(description="CSS selector")
    confidence: float = Field(description="Confidence score (0-1)")
    sample_text: str = Field(description="Sample text from this selector")
    element_count: int = Field(description="Number of elements matching this selector")