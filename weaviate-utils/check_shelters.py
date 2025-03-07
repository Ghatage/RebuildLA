#!/usr/bin/env python3
"""
Script to check if shelters are correctly loaded and accessible in Weaviate.
This script prints all shelter coordinates and tests geospatial queries.
"""

import json
import logging
import sys
import os
import argparse

# Add parent directory to path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shelter_service import get_shelter_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('check_shelters')

def check_shelters():
    """Check if shelters are properly loaded and accessible in Weaviate"""
    
    try:
        # Initialize shelter service
        logger.info("Initializing shelter service connection...")
        shelter_service = get_shelter_service()
        
        # Get all shelters
        logger.info("Fetching all shelters...")
        all_shelters = shelter_service.get_all_shelters()
        
        if not all_shelters:
            logger.error("No shelters found in Weaviate. Please run add_shelters.py first.")
            return
            
        logger.info(f"Found {len(all_shelters)} total shelters")
        
        # Print first 5 shelters
        logger.info("First 5 shelters:")
        for i, shelter in enumerate(all_shelters[:5], 1):
            logger.info(f"Shelter #{i}:")
            logger.info(f"  Name: {shelter.get('hotelname', 'N/A')}")
            logger.info(f"  Address: {shelter.get('address', 'N/A')}")
            logger.info(f"  Coordinates: ({shelter.get('lat', 'N/A')}, {shelter.get('lon', 'N/A')})")
            logger.info("")
        
        # Count coordinates
        valid_coords = 0
        zero_coords = 0
        null_coords = 0
        
        for shelter in all_shelters:
            lat = shelter.get('lat')
            lon = shelter.get('lon')
            
            if lat is None or lon is None:
                null_coords += 1
            elif lat == 0 and lon == 0:
                zero_coords += 1
            else:
                valid_coords += 1
        
        logger.info(f"Coordinate Statistics:")
        logger.info(f"  Valid Coordinates: {valid_coords}")
        logger.info(f"  Zero Coordinates (0,0): {zero_coords}")
        logger.info(f"  Null Coordinates: {null_coords}")
        
        # Test geospatial queries with known coordinates
        if valid_coords > 0:
            # Find a shelter with valid coordinates
            test_shelter = next((s for s in all_shelters if s.get('lat') and s.get('lon')), None)
            if test_shelter:
                lat = test_shelter.get('lat')
                lon = test_shelter.get('lon')
                logger.info(f"\nTesting geospatial query near ({lat}, {lon})...")
                
                # Test with different radiuses
                for radius in [1, 5, 10, 20, 50]:
                    nearby = shelter_service.get_shelters_by_location(lat, lon, distance_km=radius)
                    logger.info(f"Found {len(nearby)} shelters within {radius}km")
            else:
                logger.warning("Couldn't find a shelter with valid coordinates for testing")
        
        logger.info("\nChecking Weaviate schema...")
        schema = shelter_service.client.schema.get()
        logger.info(f"Available classes: {[c['class'] for c in schema.get('classes', [])]}")
        
        # Check if the Shelter class exists and has the location property
        shelter_class = next((c for c in schema.get('classes', []) if c['class'] == 'Shelter'), None)
        if shelter_class:
            logger.info("Shelter class found in schema")
            location_prop = next((p for p in shelter_class.get('properties', []) if p['name'] == 'location'), None)
            if location_prop:
                logger.info(f"Location property found: {location_prop}")
            else:
                logger.error("Location property not found in Shelter class")
        else:
            logger.error("Shelter class not found in schema")
            
    except Exception as e:
        logger.error(f"Error checking shelters: {str(e)}")
        logger.exception("Stack trace:")

if __name__ == "__main__":
    logger.info("SHELTER DATA CHECK")
    logger.info("==================")
    check_shelters() 