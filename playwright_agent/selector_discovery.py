"""
Selector discovery service for automatically finding CSS selectors

This module provides intelligent selector discovery by analyzing page content
and matching it with desired extraction points.
"""

import logging
import re
from typing import List, Dict, Any
from .models import ExtractionPoint, SelectorCandidate
from .playwright_client import PlaywrightClient

logger = logging.getLogger(__name__)


class SelectorDiscovery:
    """
    Service for automatically discovering CSS selectors for data extraction
    """
    
    def __init__(self):
        """Initialize the selector discovery service"""
        self.common_selectors = {
            "title": ["h1", "h2", ".title", ".heading", ".product-title", ".product-name", "[data-testid*='title']"],
            "price": [".price", ".cost", ".amount", "[data-testid*='price']", ".currency", "[class*='price']"],
            "description": [".description", ".desc", ".summary", ".content", "p", "[data-testid*='desc']"],
            "image": ["img", ".image", ".photo", ".picture", "[data-testid*='image']"],
            "link": ["a", ".link", ".url", "[href]"],
            "name": [".name", ".title", "h1", "h2", "h3", "[data-testid*='name']"],
            "text": ["p", ".text", ".content", "span", "div"],
            "number": [".number", ".count", ".quantity", "[data-testid*='number']"]
        }
    
    def _get_candidate_selectors(self, extraction_point: ExtractionPoint) -> List[str]:
        """
        Get candidate selectors based on extraction point name and type
        
        Args:
            extraction_point: The extraction point to find selectors for
            
        Returns:
            List of candidate CSS selectors
        """
        candidates = []
        
        # Add selectors based on the name (contains keywords)
        name_lower = extraction_point.name.lower()
        for keyword, selectors in self.common_selectors.items():
            if keyword in name_lower:
                candidates.extend(selectors)
        
        # Add selectors based on type
        if extraction_point.type in self.common_selectors:
            candidates.extend(self.common_selectors[extraction_point.type])
        
        # Add selectors based on description keywords
        desc_words = re.findall(r'\b\w+\b', extraction_point.description.lower())
        for word in desc_words:
            if word in self.common_selectors:
                candidates.extend(self.common_selectors[word])
        
        # Add some generic selectors that might contain the name
        name_escaped = re.escape(extraction_point.name.lower())
        candidates.extend([
            f"[class*='{extraction_point.name.lower()}']",
            f"[id*='{extraction_point.name.lower()}']",
            f"[data-testid*='{extraction_point.name.lower()}']",
            f"[aria-label*='{extraction_point.name.lower()}']"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _calculate_confidence(self, extraction_point: ExtractionPoint, 
                            selector: str, element_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a selector match
        
        Args:
            extraction_point: The extraction point
            selector: CSS selector
            element_data: Data about elements found with this selector
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        elements = element_data.get("elements", [])
        
        if not elements:
            return 0.0
        
        element = elements[0]  # Use first element for analysis
        text = element.get("text", "").lower()
        
        # Base confidence from element visibility
        if element.get("visible", False):
            confidence += 0.3
        
        # Confidence from element count (prefer unique elements)
        element_count = len(elements)
        if element_count == 1:
            confidence += 0.4
        elif element_count <= 3:
            confidence += 0.2
        
        # Confidence from text content relevance
        name_words = extraction_point.name.lower().split('_')
        desc_words = re.findall(r'\b\w+\b', extraction_point.description.lower())
        relevant_words = set(name_words + desc_words)
        
        text_words = set(re.findall(r'\b\w+\b', text))
        word_overlap = len(relevant_words.intersection(text_words))
        
        if word_overlap > 0:
            confidence += min(0.3, word_overlap * 0.1)
        
        # Type-specific confidence adjustments
        if extraction_point.type == "number":
            if re.search(r'\d+', text):
                confidence += 0.2
        elif extraction_point.type == "price":
            if re.search(r'[\$£€¥]\d+|^\d+[\$£€¥]|\d+\.\d{2}', text):
                confidence += 0.3
        elif extraction_point.type == "url":
            if "http" in text or "www." in text:
                confidence += 0.3
        
        # Selector specificity bonus
        if any(keyword in selector.lower() for keyword in name_words):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def find_selectors(self, extraction_point: ExtractionPoint, 
                           playwright_client: PlaywrightClient) -> List[SelectorCandidate]:
        """
        Find candidate selectors for an extraction point
        
        Args:
            extraction_point: The extraction point to find selectors for
            playwright_client: Client for page interaction
            
        Returns:
            List of selector candidates with confidence scores
        """
        logger.info(f"Finding selectors for extraction point: {extraction_point.name}")
        
        # If selector is already provided, validate and return it
        if extraction_point.selector:
            element_data = await playwright_client.find_elements(extraction_point.selector)
            elements = element_data.get("elements", [])
            
            if elements:
                confidence = self._calculate_confidence(extraction_point, extraction_point.selector, element_data)
                return [SelectorCandidate(
                    selector=extraction_point.selector,
                    confidence=confidence,
                    sample_text=elements[0].get("text", ""),
                    element_count=len(elements)
                )]
            else:
                logger.warning(f"Provided selector '{extraction_point.selector}' found no elements")
        
        # Get candidate selectors
        candidate_selectors = self._get_candidate_selectors(extraction_point)
        selector_candidates = []
        
        # Test each candidate selector
        for selector in candidate_selectors:
            try:
                element_data = await playwright_client.find_elements(selector)
                elements = element_data.get("elements", [])
                
                if elements:
                    confidence = self._calculate_confidence(extraction_point, selector, element_data)
                    
                    if confidence > 0.1:  # Only include candidates with reasonable confidence
                        selector_candidates.append(SelectorCandidate(
                            selector=selector,
                            confidence=confidence,
                            sample_text=elements[0].get("text", "")[:100],  # Limit sample text
                            element_count=len(elements)
                        ))
                        
            except Exception as e:
                logger.debug(f"Error testing selector '{selector}': {str(e)}")
                continue
        
        # Sort by confidence descending
        selector_candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        # Return top candidates
        top_candidates = selector_candidates[:5]
        
        logger.info(f"Found {len(top_candidates)} selector candidates for '{extraction_point.name}'")
        for candidate in top_candidates:
            logger.debug(f"  {candidate.selector}: {candidate.confidence:.2f} confidence")
        
        return top_candidates
    
    def suggest_improvements(self, extraction_point: ExtractionPoint, 
                           failed_selector: str, error_message: str) -> List[str]:
        """
        Suggest alternative selectors when the current one fails
        
        Args:
            extraction_point: The extraction point that failed
            failed_selector: The selector that failed
            error_message: Error message from the failure
            
        Returns:
            List of alternative selectors to try
        """
        logger.info(f"Suggesting improvements for failed selector: {failed_selector}")
        
        suggestions = []
        
        # If selector was too specific, try more general versions
        if "." in failed_selector and "#" not in failed_selector:
            # Try removing specific class modifiers
            base_class = failed_selector.split('.')[1].split(' ')[0]
            suggestions.append(f"[class*='{base_class}']")
        
        # If selector had no elements, try broader selectors
        if "no elements" in error_message.lower():
            name_parts = extraction_point.name.lower().split('_')
            for part in name_parts:
                suggestions.extend([
                    f"[class*='{part}']",
                    f"[id*='{part}']",
                    f"*[title*='{part}']"
                ])
        
        # Add fallback generic selectors
        if extraction_point.type == "text":
            suggestions.extend(["p", "span", "div"])
        elif extraction_point.type == "number":
            suggestions.extend(["[class*='number']", "[class*='count']", "[class*='quantity']"])
        
        # Remove duplicates
        return list(set(suggestions))