#!/usr/bin/env python3
"""
Script to reset Weaviate schema and reload the shelter data with corrected field mappings.
"""

import logging
import os
import sys
import weaviate

# Add parent directory to path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shelter_service import get_shelter_service, SHELTER_CLASS_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('reset_and_reload')

def reset_weaviate_schema():
    """Reset the Weaviate schema by deleting the shelter class"""
    try:
        # Get the Weaviate URL
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        logger.info(f"Connecting to Weaviate at {weaviate_url}")
        
        # Connect to Weaviate
        client = weaviate.Client(weaviate_url)
        
        # Check if the shelter class exists
        schema = client.schema.get()
        classes = [c['class'] for c in schema.get('classes', [])]
        
        if SHELTER_CLASS_NAME in classes:
            logger.info(f"Deleting existing {SHELTER_CLASS_NAME} class...")
            client.schema.delete_class(SHELTER_CLASS_NAME)
            logger.info(f"Successfully deleted {SHELTER_CLASS_NAME} class")
        else:
            logger.info(f"{SHELTER_CLASS_NAME} class not found, nothing to delete")
        
        logger.info("Schema reset complete")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting Weaviate schema: {str(e)}")
        return False

def main():
    """Reset Weaviate schema and reload data"""
    logger.info("Starting reset and reload process")
    
    # Step 1: Reset the schema
    if not reset_weaviate_schema():
        logger.error("Failed to reset schema, exiting")
        return
    
    # Step 2: Import the shelters with corrected field mappings
    logger.info("Importing shelters from CSV with corrected field mappings...")
    os.system("python add_shelters.py --no-sample-query")
    
    logger.info("Reset and reload process complete")
    logger.info("You can now verify the data using: curl -X GET http://127.0.0.1:6000/api/debug/shelters")

if __name__ == "__main__":
    main() 