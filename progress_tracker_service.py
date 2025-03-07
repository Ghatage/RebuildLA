import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import logging
import json
from typing import Dict, Any, Optional, List, Union

# Set up logging for this module
logger = logging.getLogger('la_fires_api.progress_tracker')

def get_progress_data() -> Dict[str, Any]:
    """
    Fetches and parses progress data from the LA Fires tracking webpage.
    
    Returns:
        Dict containing the parsed content as plain text
    """
    url = "https://www.ca.gov/lafires/track-progress/"
    
    try:
        # Step 1: Fetch the webpage content
        logger.info(f"Fetching progress data from {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Step 2: Parse HTML with BeautifulSoup using lxml parser for speed
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Step 3: Find the target div
        target_div = soup.select_one('div.col-lg-9.pt-lg-3')
        
        if not target_div:
            logger.warning("Target div not found on the webpage. Structure might have changed.")
            return {"error": "Unable to find target content on the webpage"}
        
        # Step 4: Extract and format the text content
        formatted_text = extract_formatted_text(target_div)
        
        return {
            "success": True, 
            "content": formatted_text
        }
    
    except requests.RequestException as e:
        # Handle network errors
        error_msg = f"Network error when fetching progress data: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        # Catch all other errors
        error_msg = f"Unexpected error processing progress data: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def extract_formatted_text(element) -> str:
    """
    Recursively extracts text from an HTML element while preserving logical structure.
    
    Args:
        element: BeautifulSoup element to extract text from
        
    Returns:
        Formatted plain text with appropriate line breaks
    """
    if element is None:
        return ""
    
    # Initialize an empty result string
    result = ""
    
    # Process each child element to preserve structure
    for child in element.children:
        # Skip script and style tags
        if child.name in ['script', 'style']:
            continue
            
        # If it's a string node (NavigableString)
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                result += text + " "
        
        # If it's an HTML element
        elif isinstance(child, Tag):
            # Extract text from this child
            child_text = extract_formatted_text(child)
            
            # Add appropriate line breaks based on tag type
            if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Headers get line breaks before and after
                result = result.rstrip() + "\n\n" + child_text + "\n\n"
            elif child.name == 'p':
                # Paragraphs get a line break after
                result += child_text.strip() + "\n\n"
            elif child.name == 'br':
                # Line breaks
                result += "\n"
            elif child.name in ['li']:
                # List items get a bullet point and line break
                result += "• " + child_text.strip() + "\n"
            elif child.name in ['ul', 'ol']:
                # Lists have their own formatting via list items
                result += child_text
            elif child.name == 'div':
                # Divs might be used for sections
                div_text = child_text.strip()
                if div_text:
                    result += div_text + "\n\n"
            else:
                # Other elements just add their text
                result += child_text
    
    # Clean up the result: normalize whitespace
    # Replace multiple spaces with a single space
    result = ' '.join(result.split())
    
    # Normalize line breaks (no more than 2 consecutive)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    
    return result

def process_progress_data() -> Dict[str, Any]:
    """
    Main function to be called from the API endpoint.
    Fetches, processes, and returns formatted progress data.
    
    Returns:
        Dict containing the processed data ready for API response
    """
    return get_progress_data() 