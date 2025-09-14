#!/usr/bin/env python3
"""
Example usage of the Playwright Agent for web scraping

This script demonstrates how to use the Playwright Agent to extract
data from a webpage automatically.
"""

import asyncio
import json
from playwright_agent import PlaywrightAgent, ScrapingRequest, ExtractionPoint


async def example_ecommerce_scraping():
    """
    Example: Scraping product information from an e-commerce page
    """
    print("=== E-commerce Product Scraping Example ===")
    
    # Create the agent
    agent = PlaywrightAgent()
    
    # Define what data to extract
    extraction_points = [
        ExtractionPoint(
            name="product_name",
            type="text",
            description="The main product title or name"
        ),
        ExtractionPoint(
            name="price",
            type="number",
            description="Product price in dollars"
        ),
        ExtractionPoint(
            name="description",
            type="text",
            description="Product description or summary"
        ),
        ExtractionPoint(
            name="image_url",
            type="image",
            description="Main product image URL"
        )
    ]
    
    # Create scraping request
    request = ScrapingRequest(
        url="https://example-store.com/product/123",
        extraction_points=extraction_points,
        max_iterations=3,
        output_file="ecommerce_scraper.py",
        method="auto"  # Let the agent decide
    )
    
    # Execute scraping
    result = await agent.scrape(request)
    
    # Display results
    print(f"Success: {result.success}")
    print(f"Method used: {result.method_used}")
    print(f"Iterations: {result.iterations}")
    
    if result.success:
        print("Extracted data:")
        print(json.dumps(result.data, indent=2))
        print(f"Generated script: {result.script_path}")
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def example_news_scraping():
    """
    Example: Scraping article information from a news website
    """
    print("\\n=== News Article Scraping Example ===")
    
    # Create the agent
    agent = PlaywrightAgent()
    
    # Define what data to extract
    extraction_points = [
        ExtractionPoint(
            name="headline",
            type="text",
            description="Article headline or title"
        ),
        ExtractionPoint(
            name="author",
            type="text",
            description="Article author name"
        ),
        ExtractionPoint(
            name="publish_date",
            type="text",
            description="When the article was published"
        ),
        ExtractionPoint(
            name="article_content",
            type="text",
            description="Main article content or summary"
        ),
        ExtractionPoint(
            name="tags",
            type="list",
            description="Article tags or categories"
        )
    ]
    
    # Create scraping request
    request = ScrapingRequest(
        url="https://example-news.com/article/latest-tech-news",
        extraction_points=extraction_points,
        max_iterations=3,
        output_file="news_scraper.py",
        method="browser",  # Force browser method for dynamic content
        wait_for_load=True
    )
    
    # Execute scraping
    result = await agent.scrape(request)
    
    # Display results
    print(f"Success: {result.success}")
    print(f"Method used: {result.method_used}")
    print(f"Iterations: {result.iterations}")
    
    if result.success:
        print("Extracted data:")
        print(json.dumps(result.data, indent=2))
        print(f"Generated script: {result.script_path}")
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def example_custom_selectors():
    """
    Example: Using custom CSS selectors for precise extraction
    """
    print("\\n=== Custom Selectors Example ===")
    
    # Create the agent
    agent = PlaywrightAgent()
    
    # Define extraction points with custom selectors
    extraction_points = [
        ExtractionPoint(
            name="title",
            type="text",
            description="Page title",
            selector="h1.main-title"  # Custom selector
        ),
        ExtractionPoint(
            name="subtitle",
            type="text",
            description="Page subtitle",
            selector=".subtitle"  # Custom selector
        ),
        ExtractionPoint(
            name="content_sections",
            type="list",
            description="All content section headers",
            selector="h2.section-header"  # Custom selector for list
        )
    ]
    
    # Create scraping request
    request = ScrapingRequest(
        url="https://example-blog.com/post/web-scraping-guide",
        extraction_points=extraction_points,
        max_iterations=2,
        output_file="custom_scraper.py",
        method="http"  # Force HTTP method for static content
    )
    
    # Execute scraping
    result = await agent.scrape(request)
    
    # Display results
    print(f"Success: {result.success}")
    print(f"Method used: {result.method_used}")
    print(f"Selectors used: {result.selectors_found}")
    
    if result.success:
        print("Extracted data:")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def demonstrate_page_analysis():
    """
    Example: Just analyzing a page without scraping
    """
    print("\\n=== Page Analysis Example ===")
    
    # Create the agent
    agent = PlaywrightAgent()
    
    # Analyze different types of pages
    pages_to_analyze = [
        "https://example.com",  # Simple static page
        "https://spa-example.com",  # Single page application
        "https://ecommerce-example.com/products"  # E-commerce page
    ]
    
    for url in pages_to_analyze:
        print(f"\\nAnalyzing: {url}")
        try:
            analysis = await agent.analyze_page(url)
            
            print(f"  Title: {analysis.title}")
            print(f"  Has JavaScript: {analysis.has_javascript}")
            print(f"  Load time: {analysis.load_time:.2f}s")
            print(f"  Element count: {analysis.element_count}")
            print(f"  Suggested method: {analysis.suggested_method}")
            print(f"  Confidence: {analysis.confidence:.2f}")
            print(f"  Reason: {analysis.reason}")
            
        except Exception as e:
            print(f"  Error analyzing {url}: {str(e)}")


async def main():
    """
    Run all examples
    """
    print("Playwright Agent Examples")
    print("=" * 40)
    
    try:
        # Run page analysis first
        await demonstrate_page_analysis()
        
        # Run scraping examples
        await example_ecommerce_scraping()
        await example_news_scraping()
        await example_custom_selectors()
        
        print("\\n" + "=" * 40)
        print("All examples completed!")
        
    except Exception as e:
        print(f"Error running examples: {str(e)}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())