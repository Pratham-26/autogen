"""
Tests for the Playwright Agent

These tests verify the core functionality of the agent without requiring
external dependencies like actual browser automation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import json

from playwright_agent.models import (
    ScrapingRequest, 
    ExtractionPoint, 
    PageAnalysis, 
    SelectorCandidate
)
from playwright_agent.agent import PlaywrightAgent
from playwright_agent.playwright_client import PlaywrightClient
from playwright_agent.selector_discovery import SelectorDiscovery
from playwright_agent.script_generator import ScriptGenerator


class TestModels:
    """Test data models"""
    
    def test_extraction_point_creation(self):
        """Test creating an extraction point"""
        point = ExtractionPoint(
            name="product_name",
            type="text",
            description="Product name from the page"
        )
        
        assert point.name == "product_name"
        assert point.type == "text"
        assert point.description == "Product name from the page"
        assert point.selector is None
        assert point.required is True
    
    def test_scraping_request_creation(self):
        """Test creating a scraping request"""
        extraction_points = [
            ExtractionPoint(name="title", type="text", description="Page title")
        ]
        
        request = ScrapingRequest(
            url="https://example.com",
            extraction_points=extraction_points
        )
        
        assert request.url == "https://example.com"
        assert len(request.extraction_points) == 1
        assert request.max_iterations == 5
        assert request.method == "auto"
    
    def test_page_analysis_creation(self):
        """Test creating page analysis"""
        analysis = PageAnalysis(
            title="Test Page",
            has_javascript=True,
            load_time=2.5,
            element_count=150,
            suggested_method="browser",
            confidence=0.8,
            reason="Dynamic content detected"
        )
        
        assert analysis.title == "Test Page"
        assert analysis.has_javascript is True
        assert analysis.suggested_method == "browser"
        assert analysis.confidence == 0.8


class TestPlaywrightClient:
    """Test Playwright client functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_page(self):
        """Test page analysis"""
        client = PlaywrightClient("http://localhost:3000")
        
        # Test static page
        analysis = await client.analyze_page("https://example.com")
        assert isinstance(analysis, dict)
        assert "title" in analysis
        assert "has_dynamic_content" in analysis
        
        # Test dynamic page
        analysis = await client.analyze_page("https://spa-example.com")
        assert analysis["has_dynamic_content"] is True
    
    @pytest.mark.asyncio
    async def test_find_elements(self):
        """Test finding elements"""
        client = PlaywrightClient("http://localhost:3000")
        
        result = await client.find_elements("h1")
        assert isinstance(result, dict)
        assert "selector" in result
        assert "elements" in result
        assert result["selector"] == "h1"
    
    @pytest.mark.asyncio
    async def test_extract_text(self):
        """Test text extraction"""
        client = PlaywrightClient("http://localhost:3000")
        
        text = await client.extract_text(".main-title")
        assert isinstance(text, str)


class TestSelectorDiscovery:
    """Test selector discovery functionality"""
    
    def test_get_candidate_selectors(self):
        """Test getting candidate selectors"""
        discovery = SelectorDiscovery()
        
        point = ExtractionPoint(
            name="product_price",
            type="price",
            description="Product price in dollars"
        )
        
        candidates = discovery._get_candidate_selectors(point)
        assert isinstance(candidates, list)
        assert len(candidates) > 0
        assert ".price" in candidates
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        discovery = SelectorDiscovery()
        
        point = ExtractionPoint(
            name="price",
            type="price",
            description="Product price"
        )
        
        element_data = {
            "elements": [{"text": "$29.99", "visible": True}]
        }
        
        confidence = discovery._calculate_confidence(point, ".price", element_data)
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be high for price match
    
    @pytest.mark.asyncio
    async def test_find_selectors(self):
        """Test finding selectors for extraction point"""
        discovery = SelectorDiscovery()
        
        # Mock the client
        mock_client = AsyncMock()
        mock_client.find_elements.return_value = {
            "elements": [{"text": "Sample Product", "visible": True}]
        }
        
        point = ExtractionPoint(
            name="product_name",
            type="text",
            description="Product name"
        )
        
        candidates = await discovery.find_selectors(point, mock_client)
        assert isinstance(candidates, list)
        assert all(isinstance(c, SelectorCandidate) for c in candidates)


class TestScriptGenerator:
    """Test script generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_http_script(self):
        """Test HTTP script generation"""
        generator = ScriptGenerator()
        
        extraction_points = [
            ExtractionPoint(name="title", type="text", description="Page title"),
            ExtractionPoint(name="price", type="number", description="Price")
        ]
        
        selectors = {
            "title": "h1",
            "price": ".price"
        }
        
        script = await generator.generate(
            url="https://example.com",
            extraction_points=extraction_points,
            selectors=selectors,
            method="http"
        )
        
        assert isinstance(script, str)
        assert "import requests" in script
        assert "BeautifulSoup" in script
        assert "https://example.com" in script
        assert "h1" in script
        assert ".price" in script
    
    @pytest.mark.asyncio
    async def test_generate_browser_script(self):
        """Test browser script generation"""
        generator = ScriptGenerator()
        
        extraction_points = [
            ExtractionPoint(name="title", type="text", description="Page title")
        ]
        
        selectors = {"title": "h1"}
        
        script = await generator.generate(
            url="https://example.com",
            extraction_points=extraction_points,
            selectors=selectors,
            method="browser"
        )
        
        assert isinstance(script, str)
        assert "selenium" in script
        assert "webdriver" in script
        assert "https://example.com" in script


class TestPlaywrightAgent:
    """Test main agent functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_page(self):
        """Test agent page analysis"""
        agent = PlaywrightAgent()
        
        analysis = await agent.analyze_page("https://example.com")
        assert isinstance(analysis, PageAnalysis)
        assert analysis.title
        assert analysis.suggested_method in ["http", "browser"]
        assert 0 <= analysis.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_discover_selectors(self):
        """Test agent selector discovery"""
        agent = PlaywrightAgent()
        
        extraction_points = [
            ExtractionPoint(name="title", type="text", description="Page title")
        ]
        
        # Mock the client methods
        with patch.object(agent.playwright_client, 'navigate') as mock_navigate, \
             patch.object(agent.selector_discovery, 'find_selectors') as mock_find:
            
            mock_navigate.return_value = {"success": True}
            mock_find.return_value = [
                SelectorCandidate(
                    selector="h1",
                    confidence=0.9,
                    sample_text="Sample Title",
                    element_count=1
                )
            ]
            
            result = await agent.discover_selectors("https://example.com", extraction_points)
            assert isinstance(result, dict)
            assert "title" in result
    
    @pytest.mark.asyncio
    async def test_generate_script(self):
        """Test agent script generation"""
        agent = PlaywrightAgent()
        
        request = ScrapingRequest(
            url="https://example.com",
            extraction_points=[
                ExtractionPoint(name="title", type="text", description="Page title")
            ],
            output_file="/tmp/test_script.py"
        )
        
        analysis = PageAnalysis(
            title="Test Page",
            has_javascript=False,
            load_time=1.0,
            element_count=50,
            suggested_method="http",
            confidence=0.9,
            reason="Static content"
        )
        
        selectors = {"title": "h1"}
        
        script = await agent.generate_script(request, analysis, selectors)
        assert isinstance(script, str)
        assert "import requests" in script


# Integration test
class TestIntegration:
    """Integration tests for the full pipeline"""
    
    @pytest.mark.asyncio
    async def test_full_scraping_pipeline(self):
        """Test the complete scraping pipeline"""
        agent = PlaywrightAgent()
        
        extraction_points = [
            ExtractionPoint(
                name="title",
                type="text",
                description="Page title"
            )
        ]
        
        request = ScrapingRequest(
            url="https://example.com",
            extraction_points=extraction_points,
            max_iterations=1,
            output_file="/tmp/test_scraper.py"
        )
        
        # Mock the test_script method to avoid actual script execution
        with patch.object(agent, 'test_script') as mock_test:
            mock_test.return_value = {
                "success": True,
                "data": {"title": "Example Page"},
                "missing_fields": [],
                "error": None
            }
            
            result = await agent.scrape(request)
            
            assert result.success is True
            assert "title" in result.data
            assert result.script_path == "/tmp/test_scraper.py"
            assert result.method_used in ["http", "browser"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])