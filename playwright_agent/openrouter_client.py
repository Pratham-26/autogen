"""
OpenRouter AI client for intelligent web scraping analysis

This module provides an interface to OpenRouter's API for AI-powered
page analysis, selector discovery, and script generation assistance.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from openai import AsyncOpenAI
from .models import ExtractionPoint, PageAnalysis, SelectorCandidate

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Client for OpenRouter AI services to enhance web scraping intelligence
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "anthropic/claude-3.5-sonnet"):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model to use for AI analysis
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client with OpenRouter endpoint
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        logger.info(f"OpenRouter client initialized with model: {model}")
    
    async def analyze_page_content(self, url: str, page_info: Dict[str, Any]) -> PageAnalysis:
        """
        Use AI to analyze page content and recommend scraping approach
        
        Args:
            url: URL being analyzed
            page_info: Basic page information from playwright client
            
        Returns:
            AI-enhanced page analysis
        """
        logger.info(f"AI analyzing page content for: {url}")
        
        prompt = f"""
        You are an expert web scraping analyst. Analyze the following webpage information and provide recommendations:

        URL: {url}
        Page Title: {page_info.get('title', 'Unknown')}
        Element Count: {page_info.get('element_count', 0)}
        Load Time: {page_info.get('load_time', 0)} seconds
        Has Dynamic Content: {page_info.get('has_dynamic_content', False)}
        Has JavaScript: {page_info.get('has_javascript', False)}

        Based on this information, recommend:
        1. Best scraping method (http or browser)
        2. Confidence level (0-1)
        3. Reasoning for your recommendation

        Consider:
        - Static content can usually be scraped with HTTP requests (faster)
        - Dynamic content, JavaScript-heavy sites need browser automation
        - Load time and complexity indicators
        - Modern web app patterns vs traditional websites

        Respond with a JSON object containing:
        {{
            "suggested_method": "http" or "browser",
            "confidence": 0.0-1.0,
            "reason": "explanation of your recommendation",
            "additional_insights": "any additional analysis"
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert web scraping consultant. Provide concise, actionable analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            logger.debug(f"AI analysis response: {content}")
            
            # Parse JSON response
            try:
                analysis_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to extracting JSON from response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from AI response")
            
            return PageAnalysis(
                title=page_info.get("title", ""),
                has_javascript=page_info.get("has_javascript", False),
                load_time=page_info.get("load_time", 0.0),
                element_count=page_info.get("element_count", 0),
                suggested_method=analysis_data["suggested_method"],
                confidence=float(analysis_data["confidence"]),
                reason=analysis_data["reason"]
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            # Fallback to rule-based analysis
            return self._fallback_analysis(page_info)
    
    async def discover_selectors_with_ai(self, extraction_point: ExtractionPoint, 
                                       page_html: str, existing_candidates: List[str]) -> List[SelectorCandidate]:
        """
        Use AI to analyze HTML and suggest optimal CSS selectors
        
        Args:
            extraction_point: The data point to find selectors for
            page_html: HTML content of the page (truncated for analysis)
            existing_candidates: Initial selector candidates from rule-based discovery
            
        Returns:
            AI-enhanced list of selector candidates
        """
        logger.info(f"AI discovering selectors for: {extraction_point.name}")
        
        # Truncate HTML for analysis (focus on structure)
        html_sample = page_html[:8000] if len(page_html) > 8000 else page_html
        
        prompt = f"""
        You are an expert at CSS selector discovery for web scraping. Analyze this HTML and find the best CSS selectors.

        Target Data Point:
        - Name: {extraction_point.name}
        - Type: {extraction_point.type}
        - Description: {extraction_point.description}

        HTML Sample:
        {html_sample}

        Existing Candidates: {existing_candidates}

        Find CSS selectors that would reliably extract the "{extraction_point.name}" data.
        Consider:
        1. Selector specificity vs brittleness
        2. Semantic HTML elements
        3. Class names and IDs that suggest the content type
        4. Data attributes and ARIA labels
        5. Structural patterns

        Respond with a JSON array of selector objects:
        [
            {{
                "selector": "CSS selector string",
                "confidence": 0.0-1.0,
                "reasoning": "why this selector is good",
                "sample_text": "expected text content"
            }}
        ]

        Provide up to 5 best selectors, ranked by confidence.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a web scraping expert specializing in CSS selector discovery. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            logger.debug(f"AI selector discovery response: {content}")
            
            # Parse JSON response
            try:
                selectors_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON array from response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    selectors_data = json.loads(json_match.group())
                else:
                    logger.warning("Could not parse JSON from AI selector response")
                    return []
            
            # Convert to SelectorCandidate objects
            candidates = []
            for selector_data in selectors_data:
                try:
                    candidate = SelectorCandidate(
                        selector=selector_data["selector"],
                        confidence=float(selector_data["confidence"]),
                        sample_text=selector_data.get("sample_text", ""),
                        element_count=1  # Will be updated during validation
                    )
                    candidates.append(candidate)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid selector candidate data: {e}")
                    continue
            
            logger.info(f"AI suggested {len(candidates)} selector candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"AI selector discovery failed: {str(e)}")
            return []
    
    async def improve_script_generation(self, extraction_points: List[ExtractionPoint], 
                                      selectors: Dict[str, str], method: str, 
                                      error_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Use AI to improve script generation and suggest optimizations
        
        Args:
            extraction_points: Data points to extract
            selectors: Current CSS selectors
            method: Scraping method (http or browser)
            error_context: Any error messages from previous attempts
            
        Returns:
            AI suggestions for script improvements
        """
        logger.info(f"AI improving script generation for {method} method")
        
        extraction_summary = []
        for point in extraction_points:
            selector = selectors.get(point.name, "NOT_FOUND")
            extraction_summary.append(f"- {point.name} ({point.type}): {selector}")
        
        error_section = f"\nPrevious Errors:\n{error_context}" if error_context else ""
        
        prompt = f"""
        You are an expert web scraping developer. Help improve a scraping script for better reliability and performance.

        Scraping Method: {method}
        
        Extraction Points and Selectors:
        {chr(10).join(extraction_summary)}
        {error_section}

        Provide suggestions for:
        1. Error handling improvements
        2. Selector optimization
        3. Performance enhancements
        4. Reliability measures
        5. Edge case handling

        Respond with JSON:
        {{
            "selector_improvements": {{"field_name": "improved_selector"}},
            "error_handling_suggestions": ["suggestion1", "suggestion2"],
            "performance_tips": ["tip1", "tip2"],
            "reliability_enhancements": ["enhancement1", "enhancement2"]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a web scraping expert focused on creating robust, reliable scrapers. Respond with JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                improvements = json.loads(content)
                logger.info("AI script improvements generated successfully")
                return improvements
            except json.JSONDecodeError:
                logger.warning("Could not parse AI script improvement response")
                return {}
                
        except Exception as e:
            logger.error(f"AI script improvement failed: {str(e)}")
            return {}
    
    def _fallback_analysis(self, page_info: Dict[str, Any]) -> PageAnalysis:
        """
        Fallback rule-based analysis when AI fails
        
        Args:
            page_info: Basic page information
            
        Returns:
            Rule-based page analysis
        """
        has_js = page_info.get("has_dynamic_content", False)
        load_time = page_info.get("load_time", 0.0)
        
        if has_js or load_time > 3.0:
            suggested_method = "browser"
            confidence = 0.7
            reason = "Fallback analysis: Page likely requires browser automation"
        else:
            suggested_method = "http"
            confidence = 0.8
            reason = "Fallback analysis: Static content suitable for HTTP scraping"
        
        return PageAnalysis(
            title=page_info.get("title", ""),
            has_javascript=has_js,
            load_time=load_time,
            element_count=page_info.get("element_count", 0),
            suggested_method=suggested_method,
            confidence=confidence,
            reason=reason
        )