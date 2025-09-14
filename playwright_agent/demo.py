#!/usr/bin/env python3
"""
Complete demonstration of the Playwright Agent

This script shows the full workflow of the Playwright Agent,
from analysis to script generation.
"""

import asyncio
import json
from playwright_agent import PlaywrightAgent, ScrapingRequest, ExtractionPoint


async def main():
    """Demonstrate the complete Playwright Agent workflow"""
    
    print("🎯 Playwright Agent - Complete Demonstration")
    print("=" * 60)
    
    # Initialize the agent
    agent = PlaywrightAgent()
    
    # Step 1: Define what we want to extract
    print("\n📋 Step 1: Define extraction points")
    extraction_points = [
        ExtractionPoint(
            name="main_heading",
            type="text",
            description="The main page heading"
        ),
        ExtractionPoint(
            name="price_value",
            type="number", 
            description="Any price information on the page"
        ),
        ExtractionPoint(
            name="description_text",
            type="text",
            description="Page description or summary"
        )
    ]
    
    print(f"✅ Defined {len(extraction_points)} extraction points")
    for point in extraction_points:
        print(f"   • {point.name} ({point.type}): {point.description}")
    
    # Step 2: Analyze the target page
    print("\n🔍 Step 2: Analyze target webpage")
    url = "https://example-store.com/featured-product"
    
    analysis = await agent.analyze_page(url)
    print(f"✅ Page analysis complete:")
    print(f"   • Method recommended: {analysis.suggested_method}")
    print(f"   • Confidence: {analysis.confidence:.1%}")
    print(f"   • Reason: {analysis.reason}")
    print(f"   • Has JavaScript: {analysis.has_javascript}")
    print(f"   • Load time: {analysis.load_time:.2f}s")
    
    # Step 3: Discover selectors
    print("\n🎯 Step 3: Discover CSS selectors")
    selector_candidates = await agent.discover_selectors(url, extraction_points)
    
    print("✅ Selector discovery complete:")
    for point_name, candidates in selector_candidates.items():
        if candidates:
            best = candidates[0]  # Highest confidence
            print(f"   • {point_name}: '{best.selector}' (confidence: {best.confidence:.1%})")
            print(f"     Sample: '{best.sample_text[:50]}...'")
        else:
            print(f"   • {point_name}: No suitable selectors found")
    
    # Step 4: Generate scraping script
    print("\n⚙️  Step 4: Generate scraping script")
    request = ScrapingRequest(
        url=url,
        extraction_points=extraction_points,
        max_iterations=2,
        output_file="/tmp/demo_scraper.py",
        method="auto"
    )
    
    # Get the best selectors
    selected_selectors = {}
    for point_name, candidates in selector_candidates.items():
        if candidates:
            selected_selectors[point_name] = candidates[0].selector
    
    script_content = await agent.generate_script(request, analysis, selected_selectors)
    
    print("✅ Script generation complete:")
    print(f"   • Method used: {analysis.suggested_method}")
    print(f"   • Script length: {len(script_content)} characters")
    print(f"   • Output file: {request.output_file}")
    
    # Step 5: Show script preview
    print("\n📄 Step 5: Generated script preview")
    lines = script_content.split('\n')
    
    # Show header
    print("   Script header:")
    for i, line in enumerate(lines[:10]):
        print(f"   {i+1:2}: {line}")
    
    print("   ...")
    
    # Show extraction logic
    extract_start = None
    for i, line in enumerate(lines):
        if "Extract" in line and "#" in line:
            extract_start = i
            break
    
    if extract_start:
        print("   Extraction logic:")
        for i in range(extract_start, min(extract_start + 8, len(lines))):
            print(f"   {i+1:2}: {lines[i]}")
    
    # Step 6: Summary
    print("\n✨ Step 6: Summary")
    print("✅ Complete workflow demonstrated:")
    print("   1. ✅ Page analysis and method selection")
    print("   2. ✅ Automatic selector discovery") 
    print("   3. ✅ Intelligent script generation")
    print("   4. ✅ Production-ready Python code")
    
    print(f"\n🎉 Generated script is ready to use!")
    print(f"   Run: python {request.output_file}")
    print(f"   The script will extract data as JSON")
    
    # Show what the output would look like
    print("\n📊 Expected output structure:")
    sample_output = {}
    for point in extraction_points:
        if point.name in selected_selectors:
            if point.type == "text":
                sample_output[point.name] = "Sample text content"
            elif point.type == "number":
                sample_output[point.name] = 29.99
            else:
                sample_output[point.name] = "Sample value"
        else:
            sample_output[point.name] = None
    
    print(json.dumps(sample_output, indent=2))
    
    print("\n" + "=" * 60)
    print("🎯 Playwright Agent demonstration complete!")
    print("   The agent successfully automated the entire web scraping workflow.")


if __name__ == "__main__":
    asyncio.run(main())