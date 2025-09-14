#!/usr/bin/env python3
"""
Command Line Interface for Playwright Agent

This script provides a simple CLI for using the Playwright Agent
to scrape websites from the command line.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from playwright_agent import PlaywrightAgent, ScrapingRequest, ExtractionPoint


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load scraping configuration from JSON file
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        sys.exit(1)


def create_extraction_points(config_points: List[Dict[str, Any]]) -> List[ExtractionPoint]:
    """
    Create ExtractionPoint objects from configuration
    
    Args:
        config_points: List of extraction point configurations
        
    Returns:
        List of ExtractionPoint objects
    """
    extraction_points = []
    
    for point_config in config_points:
        try:
            point = ExtractionPoint(
                name=point_config["name"],
                type=point_config["type"],
                description=point_config["description"],
                selector=point_config.get("selector"),
                required=point_config.get("required", True)
            )
            extraction_points.append(point)
        except KeyError as e:
            print(f"Error: Missing required field {e} in extraction point", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error creating extraction point: {e}", file=sys.stderr)
            sys.exit(1)
    
    return extraction_points


def create_example_config(output_path: str):
    """
    Create an example configuration file
    
    Args:
        output_path: Path where to save the example config
    """
    example_config = {
        "url": "https://example-store.com/product/123",
        "max_iterations": 5,
        "output_file": "generated_scraper.py",
        "method": "auto",
        "headless": True,
        "wait_for_load": True,
        "extraction_points": [
            {
                "name": "product_name",
                "type": "text",
                "description": "The main product title or name",
                "required": True
            },
            {
                "name": "price",
                "type": "number",
                "description": "Product price in dollars",
                "required": True
            },
            {
                "name": "description",
                "type": "text",
                "description": "Product description or summary",
                "required": False
            },
            {
                "name": "image_url",
                "type": "image",
                "description": "Main product image URL",
                "required": False
            },
            {
                "name": "features",
                "type": "list",
                "description": "List of product features",
                "required": False
            }
        ]
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(example_config, f, indent=2)
        print(f"Example configuration saved to: {output_path}")
        print("Edit this file to customize your scraping configuration.")
    except Exception as e:
        print(f"Error saving example configuration: {e}", file=sys.stderr)
        sys.exit(1)


async def run_scraping(config_path: str, verbose: bool = False):
    """
    Run the scraping process with the given configuration
    
    Args:
        config_path: Path to configuration file
        verbose: Whether to show verbose output
    """
    # Load configuration
    config = load_config(config_path)
    
    if verbose:
        print(f"Loaded configuration from: {config_path}")
        print(f"Target URL: {config['url']}")
    
    # Create extraction points
    extraction_points = create_extraction_points(config["extraction_points"])
    
    if verbose:
        print(f"Extraction points: {len(extraction_points)}")
        for point in extraction_points:
            print(f"  - {point.name} ({point.type}): {point.description}")
    
    # Create scraping request
    request = ScrapingRequest(
        url=config["url"],
        extraction_points=extraction_points,
        max_iterations=config.get("max_iterations", 5),
        output_file=config.get("output_file", "scraper_script.py"),
        method=config.get("method", "auto"),
        headless=config.get("headless", True),
        wait_for_load=config.get("wait_for_load", True)
    )
    
    # Create agent and run scraping
    agent = PlaywrightAgent()
    
    if verbose:
        print("\\nStarting scraping process...")
    
    try:
        result = await agent.scrape(request)
        
        # Display results
        print("\\n" + "=" * 50)
        print("SCRAPING RESULTS")
        print("=" * 50)
        
        print(f"Success: {result.success}")
        print(f"Method used: {result.method_used}")
        print(f"Iterations: {result.iterations}")
        print(f"Script generated: {result.script_path}")
        
        if result.success:
            print("\\nExtracted data:")
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
            
            print("\\nSelectors discovered:")
            for name, selector in result.selectors_found.items():
                print(f"  {name}: {selector}")
                
            print(f"\\nGenerated script saved to: {result.script_path}")
            print("You can now run this script independently to scrape the data.")
            
        else:
            print(f"\\nError: {result.error_message}")
            
            if result.selectors_found:
                print("\\nSelectors that were tried:")
                for name, selector in result.selectors_found.items():
                    print(f"  {name}: {selector}")
    
    except Exception as e:
        print(f"\\nError during scraping: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """
    Main CLI entry point
    """
    parser = argparse.ArgumentParser(
        description="Playwright Agent - Intelligent Web Scraping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create example configuration
  python cli.py --example-config my_config.json
  
  # Run scraping with configuration
  python cli.py --config my_config.json
  
  # Run with verbose output
  python cli.py --config my_config.json --verbose
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to JSON configuration file"
    )
    
    parser.add_argument(
        "--example-config", "-e",
        type=str,
        help="Create an example configuration file at the specified path"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output during scraping"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Playwright Agent 0.1.0"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.example_config:
        create_example_config(args.example_config)
        return
    
    if not args.config:
        parser.error("Either --config or --example-config is required")
    
    # Run scraping
    try:
        asyncio.run(run_scraping(args.config, args.verbose))
    except KeyboardInterrupt:
        print("\\nScraping interrupted by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()