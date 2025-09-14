# Playwright Agent

An intelligent web scraping agent built with AutoGen and enhanced with OpenRouter AI that automatically determines the best approach for extracting data from web pages. It uses the Playwright MCP (Model Context Protocol) server for browser automation, combining existing tools with AI decision-making to create robust scraping solutions without building tools from scratch.

## What is this Agent?

This is an intelligent web scraping agent built with AutoGen and enhanced with OpenRouter AI that automatically determines the best approach for extracting data from web pages. It uses the Playwright MCP (Model Context Protocol) server for browser automation, combining existing tools with AI decision-making to create robust scraping solutions without building tools from scratch.

## What does it do?

The agent takes a URL and a list of data points to extract, then:

1. **AI-Powered Page Analysis** using OpenRouter models for intelligent method selection
2. **Determines the best scraping method** (simple HTTP requests vs full browser automation)
3. **AI-Enhanced Selector Discovery** for the data you want to extract using advanced pattern recognition
4. **Generates optimized Python scripts** with AI-suggested improvements
5. **Tests and improves** the script iteratively until it works correctly
6. **Outputs a ready-to-use Python script** that extracts data as JSON

## Key Features

- **🧠 AI-Powered Analysis**: Uses OpenRouter's advanced models for intelligent page analysis
- **🎯 Smart Method Selection**: AI determines optimal approach (HTTP vs browser automation)
- **🔍 AI-Enhanced Selector Discovery**: Combines rule-based and AI-driven selector finding
- **⚙️ Intelligent Script Generation**: AI-optimized Python scripts with advanced error handling
- **🔄 Iterative Improvement**: Automatically fixes and improves scripts using AI feedback
- **📋 Production Ready**: Generates complete scripts with robust error handling and proper data formatting

## Installation

Since this agent is designed to be standalone and not import from existing AutoGen code, you can use it independently:

```bash
# Navigate to the playwright_agent directory
cd playwright_agent

# Install required dependencies
pip install -r requirements.txt
```

## OpenRouter Setup

To enable AI-powered features, you need an OpenRouter API key:

1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Get your API key from the dashboard
3. Set the environment variable:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

The agent will work without an API key but will use rule-based analysis instead of AI-powered intelligence.

## Usage

### Basic Example with AI Integration

```python
import asyncio
import os
from playwright_agent import PlaywrightAgent, ScrapingRequest, ExtractionPoint, OpenRouterConfig

async def main():
    # Configure OpenRouter (optional - will use rule-based if not provided)
    openrouter_config = OpenRouterConfig(
        api_key=os.getenv("OPENROUTER_API_KEY"),  # or your API key directly
        model="anthropic/claude-3.5-sonnet",      # recommended model
        enabled=True
    )
    
    # Create the agent with AI integration
    agent = PlaywrightAgent(openrouter_config=openrouter_config)
    
    # Define what data to extract
    extraction_points = [
        ExtractionPoint(
            name="product_name",
            type="text",
            description="The main product title"
        ),
        ExtractionPoint(
            name="price",
            type="number", 
            description="Product price with currency"
        )
    ]
    
    # Create scraping request
    request = ScrapingRequest(
        url="https://example-store.com/product/123",
        extraction_points=extraction_points,
        max_iterations=5,
        output_file="scraper_script.py"
    )
    
    # Execute scraping
    result = await agent.scrape(request)
    
    if result.success:
        print("Extracted data:", result.data)
        print("Generated script:", result.script_path)
    else:
        print("Error:", result.error_message)

# Run the example
asyncio.run(main())
```

### Input Format

```json
{
  "url": "https://example.com/page",
  "max_iterations": 5,
  "output_file": "scraper_script.py",
  "extraction_points": [
    {
      "name": "product_name",
      "type": "text",
      "description": "The main product title"
    },
    {
      "name": "price",
      "type": "number", 
      "description": "Product price with currency"
    }
  ]
}
```

### Extraction Point Types

- **text**: Extract text content from elements
- **number**: Extract numeric values (with automatic parsing)
- **url**: Extract URLs from href attributes or text
- **image**: Extract image URLs from src attributes
- **list**: Extract multiple items as a list

### Scraping Methods

- **auto** (default): Agent automatically chooses the best method
- **http**: Use HTTP requests with BeautifulSoup (faster, for static content)
- **browser**: Use Selenium WebDriver (for dynamic content requiring JavaScript)

## Examples

Run the included examples to see the agent in action:

```bash
python examples.py
```

This will demonstrate:
- E-commerce product scraping
- News article extraction
- Custom selector usage
- Page analysis

## Output

The agent generates:
- A working Python script (e.g., `scraper_script.py`)
- JSON data extracted from the webpage
- Success/failure report with details

Example generated script structure:

```python
#!/usr/bin/env python3
"""
Auto-generated web scraping script
Generated by Playwright Agent
"""

import json
import requests
from bs4 import BeautifulSoup

def extract_data(url: str):
    # ... generated extraction logic
    return data

def main():
    url = "https://example.com"
    result = extract_data(url)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

## Architecture

The agent consists of several components:

### Core Components

1. **PlaywrightAgent** (`agent.py`): Main orchestrator that coordinates the scraping process
2. **PlaywrightClient** (`playwright_client.py`): Interface to Playwright MCP server for browser automation
3. **SelectorDiscovery** (`selector_discovery.py`): Automatically finds CSS selectors for extraction points
4. **ScriptGenerator** (`script_generator.py`): Generates production-ready Python scraping scripts

### Data Models

- **ScrapingRequest**: Input configuration for scraping
- **ScrapingResult**: Output with extracted data and metadata
- **ExtractionPoint**: Definition of data points to extract
- **PageAnalysis**: Analysis results for webpage structure
- **SelectorCandidate**: Potential CSS selectors with confidence scores

## Technologies Used

- **AutoGen**: AI agent framework for decision making (architectural pattern)
- **Playwright MCP Server**: Pre-built Model Context Protocol server for browser automation and page analysis
- **Python Tools**: Script generation and execution
- **Selenium**: For complex dynamic website scraping (generated scripts)
- **HTTP Requests**: For simple static website scraping (generated scripts)
- **BeautifulSoup**: HTML parsing for HTTP-based scraping
- **Pydantic**: Data validation and serialization

*Note: Uses existing Playwright MCP server rather than building browser automation tools from scratch.*

## Use Cases

- E-commerce product data extraction
- News article scraping
- Real estate listing data
- Social media content extraction
- Any structured data from websites

The agent handles the complexity of web scraping so you just need to describe what data you want and from which URL.

## Error Handling

The agent includes comprehensive error handling:
- Network timeouts and connection errors
- Missing elements and selector failures
- JavaScript execution errors
- Data parsing and validation errors
- Automatic retry with improved selectors

## Limitations

- Requires Playwright MCP server to be running (simulated in current implementation)
- Generated scripts require appropriate dependencies (requests/beautifulsoup4 or selenium)
- Some complex dynamic sites may require manual selector refinement
- Rate limiting and anti-bot measures may affect success rates

## Contributing

This is a standalone demonstration of using AutoGen framework for complex agent building. To extend functionality:

1. Add new extraction types in `models.py`
2. Enhance selector discovery algorithms in `selector_discovery.py`
3. Improve script generation templates in `script_generator.py`
4. Add new analysis capabilities in `playwright_client.py`