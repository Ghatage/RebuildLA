#!/usr/bin/env python3
"""
Script to demonstrate querying shelters from Weaviate.
This script shows various query examples.
"""

import json
import logging
import sys
import os

# Add parent directory to path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shelter_service import get_shelter_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('query_shelters')

def display_shelter(shelter, index=None):
    """Format and display a shelter nicely"""
    prefix = f"Shelter #{index}: " if index is not None else "Shelter: "
    
    print(f"\n{prefix}{shelter.get('hotelname', shelter.get('address', 'Unknown'))}")
    print("-" * 80)
    print(f"Address: {shelter.get('address', 'N/A')}")
    print(f"Phone: {shelter.get('phonenumber', 'N/A')}")
    print(f"Booking Link: {shelter.get('bookinglink', 'N/A')}")
    print(f"Location: ({shelter.get('lat', 'N/A')}, {shelter.get('lon', 'N/A')})")
    
    if shelter.get('notes'):
        print(f"Notes: {shelter.get('notes')}")
    print("-" * 80)

def main():
    """Run example queries against Weaviate"""
    
    try:
        # Initialize shelter service
        logger.info("Initializing shelter service connection...")
        shelter_service = get_shelter_service()
        
        print("\n===== SHELTER QUERY EXAMPLES =====\n")
        
        # Example 1: Get all shelters
        print("\n1. GETTING ALL SHELTERS")
        all_shelters = shelter_service.get_all_shelters()
        
        if not all_shelters:
            print("No shelters found. Please run add_sample_shelters.py first.")
            return
            
        print(f"Found {len(all_shelters)} total shelters")
        
        # Show first 3 shelters
        for i, shelter in enumerate(all_shelters[:3], 1):
            display_shelter(shelter, i)
            
        # Example 2: Geospatial query using the first shelter's coordinates
        print("\n2. NEARBY SHELTER SEARCH (GEOSPATIAL)")
        
        # Use the first shelter as our reference point
        reference_shelter = all_shelters[0]
        lat = reference_shelter["lat"]
        lon = reference_shelter["lon"]
        
        print(f"Searching for shelters near ({lat}, {lon})...")
        
        # Query for nearby shelters (10km radius)
        nearby_shelters = shelter_service.get_shelters_by_location(lat, lon, distance_km=10.0)
        
        print(f"Found {len(nearby_shelters)} shelters within 10km")
        
        # Show the first 3 nearby shelters
        for i, shelter in enumerate(nearby_shelters[:3], 1):
            display_shelter(shelter, i)
            
        # Example 3: Raw JSON format (useful for API responses)
        print("\n3. JSON FORMAT EXAMPLE (FIRST SHELTER)")
        
        if all_shelters:
            print(json.dumps(all_shelters[0], indent=2))
        
    except Exception as e:
        logger.error(f"Error querying shelters: {str(e)}")

if __name__ == "__main__":
    main() 