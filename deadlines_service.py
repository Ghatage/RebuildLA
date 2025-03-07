import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List
import datetime
import re

# Set up logging for this module
logger = logging.getLogger('la_fires_api.deadlines')

def get_deadlines_data() -> Dict[str, Any]:
    """
    Fetches and parses deadlines data from the LA Fires webpage.
    
    Returns:
        Dict containing parsed deadlines with dates and descriptions
    """
    url = "https://www.ca.gov/lafires/"
    
    try:
        # Step 1: Fetch the webpage content
        logger.info(f"Fetching deadlines data from {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Step 2: Parse HTML with BeautifulSoup using lxml parser for speed
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Step 3: Find all divs with class "col-lg-3" that contain deadline information
        deadline_divs = soup.find_all('div', class_='col-lg-3')
        
        if not deadline_divs:
            logger.warning("No deadline divs found on the webpage. Structure might have changed.")
            return {"success": False, "error": "Unable to find deadline content on the webpage"}
        
        # Step 4: Extract deadline data from each div
        deadlines = extract_deadlines(deadline_divs)
        
        # Sort deadlines by date
        deadlines.sort(key=lambda x: x.get('date_obj', datetime.datetime.max))
        
        # Remove datetime objects used for sorting
        for deadline in deadlines:
            if 'date_obj' in deadline:
                del deadline['date_obj']
        
        return {
            "success": True,
            "deadlines": deadlines,
            "count": len(deadlines)
        }
    
    except requests.RequestException as e:
        # Handle network errors
        error_msg = f"Network error when fetching deadlines data: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        # Catch all other errors
        error_msg = f"Unexpected error processing deadlines data: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def extract_deadlines(deadline_divs) -> List[Dict[str, Any]]:
    """
    Extract deadline information from the div elements
    
    Args:
        deadline_divs: List of BeautifulSoup elements containing deadline info
        
    Returns:
        List of dictionaries containing structured deadline data
    """
    deadlines = []
    
    for div in deadline_divs:
        try:
            # Extract the date from h3 element
            date_elem = div.find('h3', class_='font-size-20')
            if not date_elem:
                continue
                
            date_text = date_elem.get_text().strip()
            
            # Extract the description from p element
            desc_elem = div.find('p')
            if not desc_elem:
                continue
                
            # Extract text and handle any contained links
            description = ""
            link_url = None
            
            for content in desc_elem.contents:
                if isinstance(content, str):
                    description += content.strip() + " "
                elif content.name == 'a':
                    # Include link text but not the external link icon
                    link_text = content.get_text().strip()
                    # Store the link URL
                    link_url = content.get('href')
                    # Remove span with external-link-icon if present
                    span = content.find('span', class_='external-link-icon')
                    if span:
                        link_text = link_text.replace(span.get_text(), '').strip()
                    description += link_text + " "
            
            description = description.strip()
            
            # Fix common formatting issues
            description = re.sub(r'for(\w)', r'for \1', description)  # Add space after "for" if missing
            description = re.sub(r'\s+', ' ', description)  # Normalize spaces
            
            # Try to parse the date to enable sorting
            date_obj = None
            try:
                # Extract month, day, year from date string like "March 10, 2025"
                date_match = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', date_text)
                if date_match:
                    month, day, year = date_match.groups()
                    month_num = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                                "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}.get(month)
                    if month_num:
                        date_obj = datetime.datetime(int(year), month_num, int(day))
            except Exception as e:
                logger.warning(f"Error parsing date '{date_text}': {str(e)}")
            
            deadline = {
                "date": date_text,
                "description": description
            }
            
            # Add date object for sorting (will be removed later)
            if date_obj:
                deadline["date_obj"] = date_obj
            
            # Add link URL if available
            if link_url:
                deadline["link"] = link_url
            
            deadlines.append(deadline)
            
        except Exception as e:
            logger.warning(f"Error extracting deadline data: {str(e)}")
            continue
    
    return deadlines

def process_deadlines_data() -> Dict[str, Any]:
    """
    Main function to be called from the API endpoint.
    Fetches, processes, and returns formatted deadlines data.
    
    Returns:
        Dict containing the processed deadlines ready for API response
    """
    return get_deadlines_data() 