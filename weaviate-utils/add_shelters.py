#!/usr/bin/env python3
"""
Script to load shelter data from geocoded.csv into Weaviate.

Usage:
  python add_shelters.py [--no-sample-query]

Options:
  --no-sample-query  Skip running the sample query after import
"""

import csv
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
logger = logging.getLogger('add_csv_shelters')

# Path to the CSV file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(SCRIPT_DIR, 'geocoded.csv')

# Global variable to store the first shelter for sample query
first_shelter = None

def load_shelters_from_csv(csv_file):
    """
    Load shelter data from a CSV file
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        List of shelter dictionaries
    """
    global first_shelter
    shelters = []
    skipped_rows = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            row_count = 0
            for row in reader:
                row_count += 1
                
                # Handle misaligned CSV data
                # The actual format appears to be:
                # address, bookinglink, phonenumber (in lat column), latitude (in lon column), 
                # longitude (in phonenumber column), notes (in notes column)
                try:
                    # Extract latitude and longitude from misaligned columns
                    latitude_str = row.get("lon", "").strip()
                    longitude_str = row.get("phonenumber", "").strip()
                    
                    # Skip if either coordinate is missing
                    if not latitude_str or not longitude_str:
                        logger.warning(f"Skipping row {row_count}: Missing coordinates")
                        skipped_rows += 1
                        continue
                    
                    # Try to convert to float
                    lat = float(latitude_str)
                    lon = float(longitude_str)
                    
                    # Create the shelter object with correct field mapping
                    # The hotelname is not in the CSV, so we'll use the address as hotelname
                    shelter = {
                        "hotelname": row.get("address", "").strip(),
                        "address": row.get("address", "").strip(),
                        "bookinglink": row.get("bookinglink", "").strip(),
                        "lat": lat,
                        "lon": lon,
                        "phonenumber": row.get("lat", "").strip(),  # phonenumber is in lat column
                        "notes": row.get("notes", "").strip()
                    }
                    
                    # Store first valid row for sample query
                    if first_shelter is None:
                        first_shelter = shelter.copy()
                    
                    shelters.append(shelter)
                    
                except ValueError:
                    logger.warning(f"Skipping row {row_count}: Invalid coordinates format")
                    skipped_rows += 1
                    continue
                
            logger.info(f"Loaded {len(shelters)} shelters from CSV (skipped {skipped_rows} rows with invalid coordinates)")
            return shelters
            
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        return []

def main():
    """Load shelters from CSV and add them to Weaviate"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Import shelters from CSV into Weaviate')
    parser.add_argument('--no-sample-query', action='store_true', help='Skip running the sample query after import')
    args = parser.parse_args()
    
    try:
        # Initialize shelter service
        logger.info("Initializing shelter service...")
        shelter_service = get_shelter_service()
        
        # Create schema if it doesn't exist
        logger.info("Creating schema...")
        schema_created = shelter_service.create_schema()
        if not schema_created:
            logger.error("Failed to create schema. Exiting.")
            return
            
        # Load shelters from CSV
        logger.info(f"Loading shelters from {CSV_FILE}...")
        shelters = load_shelters_from_csv(CSV_FILE)
        
        if not shelters:
            logger.error("No valid shelters loaded from CSV. Exiting.")
            return
            
        # Add shelters to Weaviate
        logger.info(f"Adding {len(shelters)} shelters to Weaviate...")
        successful_imports = 0
        failed_imports = 0
        
        for i, shelter in enumerate(shelters):
            shelter_id = shelter_service.add_shelter(shelter)
            if shelter_id:
                successful_imports += 1
                if i < 5:  # Log only the first 5 for brevity
                    logger.info(f"Added shelter: {shelter.get('hotelname', shelter.get('address', 'Unknown'))} (ID: {shelter_id})")
            else:
                failed_imports += 1
                if i < 5:  # Log only the first 5 for brevity
                    logger.warning(f"Failed to add shelter: {shelter.get('hotelname', shelter.get('address', 'Unknown'))}")
                
        logger.info(f"Import summary: {successful_imports} successful, {failed_imports} failed")
        
        # Run a sample query using the first shelter's coordinates
        if not args.no_sample_query and first_shelter is not None:
            logger.info("\n--- Sample Query ---")
            lat = first_shelter["lat"]
            lon = first_shelter["lon"]
            
            logger.info(f"Querying shelters near coordinates: ({lat}, {lon})")
            nearby_shelters = shelter_service.get_shelters_by_location(lat, lon, distance_km=10.0)
            
            logger.info(f"Found {len(nearby_shelters)} nearby shelters")
            
            # Display the first result
            if nearby_shelters:
                logger.info("First result:")
                logger.info(json.dumps(nearby_shelters[0], indent=2))
        
    except Exception as e:
        logger.error(f"Error adding shelters: {str(e)}")

if __name__ == "__main__":
    main() 