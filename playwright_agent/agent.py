"""
Main Playwright Agent implementation

This module contains the core agent that orchestrates web scraping using
the Playwright MCP server and AutoGen framework.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import (
    ScrapingRequest, 
    ScrapingResult, 
    ExtractionPoint, 
    PageAnalysis, 
    SelectorCandidate
)
from .playwright_client import PlaywrightClient
from .script_generator import ScriptGenerator
from .selector_discovery import SelectorDiscovery

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightAgent:
    """
    An intelligent web scraping agent that combines AutoGen's decision-making
    capabilities with Playwright MCP server for browser automation.
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:3000"):
        """
        Initialize the Playwright Agent
        
        Args:
            mcp_server_url: URL of the Playwright MCP server
        """
        self.mcp_server_url = mcp_server_url
        self.playwright_client = PlaywrightClient(mcp_server_url)
        self.script_generator = ScriptGenerator()
        self.selector_discovery = SelectorDiscovery()
        
    async def analyze_page(self, url: str) -> PageAnalysis:
        """
        Analyze a webpage to determine the best scraping approach
        
        Args:
            url: URL to analyze
            
        Returns:
            PageAnalysis with recommended approach
        """
        logger.info(f"Analyzing page: {url}")
        
        # Use Playwright MCP to navigate and analyze the page
        page_info = await self.playwright_client.analyze_page(url)
        
        # Determine if JavaScript is needed
        has_js = page_info.get("has_dynamic_content", False)
        load_time = page_info.get("load_time", 0.0)
        element_count = page_info.get("element_count", 0)
        
        # Decision logic for method selection
        if has_js or load_time > 3.0:
            suggested_method = "browser"
            confidence = 0.8 if has_js else 0.6
            reason = "Page has dynamic content requiring JavaScript" if has_js else "Slow loading page, browser needed"
        else:
            suggested_method = "http"
            confidence = 0.9
            reason = "Static content can be scraped with simple HTTP requests"
            
        return PageAnalysis(
            title=page_info.get("title", ""),
            has_javascript=has_js,
            load_time=load_time,
            element_count=element_count,
            suggested_method=suggested_method,
            confidence=confidence,
            reason=reason
        )
    
    async def discover_selectors(self, url: str, extraction_points: List[ExtractionPoint]) -> Dict[str, List[SelectorCandidate]]:
        """
        Automatically discover CSS selectors for extraction points
        
        Args:
            url: URL to analyze
            extraction_points: List of data points to find selectors for
            
        Returns:
            Dictionary mapping extraction point names to selector candidates
        """
        logger.info(f"Discovering selectors for {len(extraction_points)} extraction points")
        
        # Navigate to the page using Playwright MCP
        await self.playwright_client.navigate(url)
        
        selector_candidates = {}
        
        for point in extraction_points:
            logger.info(f"Finding selectors for: {point.name}")
            
            # Use the selector discovery service to find candidates
            candidates = await self.selector_discovery.find_selectors(
                point, self.playwright_client
            )
            
            selector_candidates[point.name] = candidates
            
        return selector_candidates
    
    async def generate_script(self, request: ScrapingRequest, analysis: PageAnalysis, 
                            selectors: Dict[str, str]) -> str:
        """
        Generate a Python script for scraping based on analysis and selectors
        
        Args:
            request: Original scraping request
            analysis: Page analysis results
            selectors: Discovered selectors for each extraction point
            
        Returns:
            Generated Python script as string
        """
        logger.info(f"Generating script using {analysis.suggested_method} method")
        
        # Determine actual method to use
        if request.method == "auto":
            method = analysis.suggested_method
        else:
            method = request.method
            
        # Generate the script
        script_content = await self.script_generator.generate(
            url=request.url,
            extraction_points=request.extraction_points,
            selectors=selectors,
            method=method,
            headless=request.headless,
            wait_for_load=request.wait_for_load
        )
        
        # Save the script
        script_path = Path(request.output_file)
        script_path.write_text(script_content)
        
        logger.info(f"Script saved to: {script_path}")
        return script_content
    
    async def test_script(self, script_path: str, expected_fields: List[str]) -> Dict[str, Any]:
        """
        Test the generated script and validate the results
        
        Args:
            script_path: Path to the generated script
            expected_fields: List of expected field names in the output
            
        Returns:
            Test results including extracted data and validation status
        """
        logger.info(f"Testing script: {script_path}")
        
        try:
            # Execute the script in a subprocess
            import subprocess
            import sys
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    # Parse the JSON output
                    data = json.loads(result.stdout)
                    
                    # Validate that all expected fields are present
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    return {
                        "success": len(missing_fields) == 0,
                        "data": data,
                        "missing_fields": missing_fields,
                        "error": None
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "data": {},
                        "missing_fields": expected_fields,
                        "error": f"Invalid JSON output: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "data": {},
                    "missing_fields": expected_fields,
                    "error": f"Script execution failed: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "data": {},
                "missing_fields": expected_fields,
                "error": "Script execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "data": {},
                "missing_fields": expected_fields,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def scrape(self, request: ScrapingRequest) -> ScrapingResult:
        """
        Main entry point for scraping a webpage
        
        Args:
            request: Scraping configuration
            
        Returns:
            ScrapingResult with extracted data and metadata
        """
        logger.info(f"Starting scraping process for: {request.url}")
        
        try:
            # Step 1: Analyze the page
            analysis = await self.analyze_page(request.url)
            logger.info(f"Page analysis complete: {analysis.suggested_method} (confidence: {analysis.confidence})")
            
            # Step 2: Discover selectors for extraction points
            selector_candidates = await self.discover_selectors(request.url, request.extraction_points)
            
            # Select the best selector for each extraction point
            selected_selectors = {}
            for point_name, candidates in selector_candidates.items():
                if candidates:
                    # Select the candidate with highest confidence
                    best_candidate = max(candidates, key=lambda c: c.confidence)
                    selected_selectors[point_name] = best_candidate.selector
                else:
                    logger.warning(f"No selector found for: {point_name}")
                    
            # Step 3: Generate script
            script_content = await self.generate_script(request, analysis, selected_selectors)
            
            # Step 4: Test and iterate
            iterations = 0
            last_test_result = None
            
            while iterations < request.max_iterations:
                iterations += 1
                logger.info(f"Testing iteration {iterations}")
                
                expected_fields = [point.name for point in request.extraction_points]
                test_result = await self.test_script(request.output_file, expected_fields)
                last_test_result = test_result
                
                if test_result["success"]:
                    logger.info("Script test successful!")
                    break
                else:
                    logger.warning(f"Script test failed: {test_result['error']}")
                    
                    # If not the last iteration, try to improve the script
                    if iterations < request.max_iterations:
                        logger.info("Attempting to improve script...")
                        # Here we could implement logic to improve selectors or method
                        # For now, we'll break to avoid infinite loops
                        break
            
            # Prepare final result
            if last_test_result and last_test_result["success"]:
                return ScrapingResult(
                    success=True,
                    data=last_test_result["data"],
                    script_path=request.output_file,
                    method_used=analysis.suggested_method,
                    iterations=iterations,
                    selectors_found=selected_selectors
                )
            else:
                return ScrapingResult(
                    success=False,
                    data={},
                    script_path=request.output_file,
                    method_used=analysis.suggested_method,
                    iterations=iterations,
                    error_message=last_test_result["error"] if last_test_result else "Unknown error",
                    selectors_found=selected_selectors
                )
                
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return ScrapingResult(
                success=False,
                data={},
                script_path=request.output_file,
                method_used="unknown",
                iterations=0,
                error_message=str(e),
                selectors_found={}
            )