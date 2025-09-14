#!/usr/bin/env python3
"""
Complete demonstration of the Playwright Agent with OpenRouter AI

This script shows the full workflow of the Playwright Agent,
from AI-powered analysis to intelligent script generation.
"""

import asyncio
import json
import os
from playwright_agent import PlaywrightAgent, ScrapingRequest, ExtractionPoint, OpenRouterConfig


async def main():
    """Demonstrate the complete Playwright Agent workflow with AI integration"""
    
    print("🎯 Playwright Agent - Complete Demonstration with OpenRouter AI")
    print("=" * 70)
    
    # Check for OpenRouter API key
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_api_key:
        print("✅ OpenRouter API key found - AI features enabled")
        openrouter_config = OpenRouterConfig(
            api_key=openrouter_api_key,
            model="anthropic/claude-3.5-sonnet",
            enabled=True
        )
    else:
        print("⚠️  No OpenRouter API key found - using rule-based analysis")
        print("   Set OPENROUTER_API_KEY environment variable to enable AI features")
        openrouter_config = OpenRouterConfig(enabled=False)
    
    # Initialize the agent with OpenRouter configuration
    agent = PlaywrightAgent(openrouter_config=openrouter_config)
    
    # Step 1: Define what we want to extract
    print("\n📋 Step 1: Define extraction points")
    extraction_points = [
        ExtractionPoint(
            name="main_heading",
            type="text",
            description="The main product title or page heading"
        ),
        ExtractionPoint(
            name="price_value",
            type="number", 
            description="Current product price in dollars"
        ),
        ExtractionPoint(
            name="description_text",
            type="text",
            description="Product description or summary text"
        )
    ]
    
    print(f"✅ Defined {len(extraction_points)} extraction points")
    for point in extraction_points:
        print(f"   • {point.name} ({point.type}): {point.description}")
    
    # Step 2: Analyze the target page with AI
    print("\n🧠 Step 2: AI-powered page analysis")
    url = "https://example-store.com/featured-product"
    
    analysis = await agent.analyze_page(url)
    print(f"✅ Page analysis complete:")
    print(f"   • Method recommended: {analysis.suggested_method}")
    print(f"   • Confidence: {analysis.confidence:.1%}")
    print(f"   • Reason: {analysis.reason}")
    print(f"   • Has JavaScript: {analysis.has_javascript}")
    print(f"   • Load time: {analysis.load_time:.2f}s")
    
    if agent.ai_enabled:
        print("   • Analysis enhanced with OpenRouter AI 🤖")
    else:
        print("   • Analysis using rule-based logic")
    
    # Step 3: AI-enhanced selector discovery
    print("\n🎯 Step 3: AI-enhanced selector discovery")
    selector_candidates = await agent.discover_selectors(url, extraction_points)
    
    print("✅ Selector discovery complete:")
    for point_name, candidates in selector_candidates.items():
        if candidates:
            best = candidates[0]  # Highest confidence
            print(f"   • {point_name}: '{best.selector}' (confidence: {best.confidence:.1%})")
            print(f"     Sample: '{best.sample_text[:50]}...'")
            if len(candidates) > 1:
                print(f"     {len(candidates)-1} additional candidates found")
        else:
            print(f"   • {point_name}: No suitable selectors found")
    
    if agent.ai_enabled:
        print("   • Selectors enhanced with AI analysis 🤖")
    
    # Step 4: Generate AI-enhanced scraping script
    print("\n⚙️  Step 4: Generate AI-enhanced scraping script")
    request = ScrapingRequest(
        url=url,
        extraction_points=extraction_points,
        max_iterations=2,
        output_file="/tmp/ai_enhanced_scraper.py",
        method="auto",
        openrouter_config=openrouter_config
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
    
    if agent.ai_enabled:
        print("   • Script enhanced with OpenRouter AI optimizations 🤖")
    
    # Step 5: Show enhanced script preview
    print("\n📄 Step 5: AI-enhanced script preview")
    lines = script_content.split('\n')
    
    # Show header (first 20 lines)
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