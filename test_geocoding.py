#!/usr/bin/env python3
"""
Test script for Mapbox geocoding functionality
"""

import os
import requests
import json
from pprint import pprint

def geocode_address(address):
    """Test geocoding an address using Mapbox API"""
    
    # Get Mapbox API key from environment
    mapbox_token = os.getenv("MAPBOX_ACCESS_TOKEN")
    if not mapbox_token:
        print("ERROR: MAPBOX_ACCESS_TOKEN environment variable not set")
        return None
    
    # URL encode the address
    encoded_address = requests.utils.quote(address)
    
    # Construct Mapbox Geocoding API URL
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"
    params = {
        "access_token": mapbox_token,
        "limit": 1,
        "country": "US"
    }
    
    print(f"Geocoding address: {address}")
    print(f"API URL: {url}")
    
    # Make request to Mapbox
    response = requests.get(url, params=params)
    
    # Check response
    if response.status_code != 200:
        print(f"ERROR: Mapbox API returned status code {response.status_code}")
        print(response.text)
        return None
    
    # Parse response
    data = response.json()
    
    # Pretty print the full response for inspection
    print("\nFull Mapbox Response:")
    pprint(data)
    
    # Check if we got features back
    if not data.get("features") or len(data["features"]) == 0:
        print(f"WARNING: No geocoding results found for address: {address}")
        return None
    
    # Get coordinates [longitude, latitude]
    coordinates = data["features"][0]["center"]
    
    # Return as (latitude, longitude) - note the order reversal from Mapbox's format
    return (coordinates[1], coordinates[0])

def test_addresses():
    """Test geocoding with various addresses"""
    
    test_cases = [
        "123 Main St",
        "456 Hollywood Blvd",
        "789 Sunset Blvd, Los Angeles",
        "1000 Wilshire Blvd, Los Angeles, CA",
        "Santa Monica Pier",
        "Griffith Observatory",
        "LAX Airport"
    ]
    
    for address in test_cases:
        print("\n" + "="*50)
        print(f"Testing address: {address}")
        
        # Geocode the address
        result = geocode_address(address)
        
        if result:
            lat, lon = result
            print(f"SUCCESS: Geocoded to coordinates: ({lat}, {lon})")
        else:
            print("FAILED: Could not geocode address")
        
        print("="*50)

if __name__ == "__main__":
    print("MAPBOX GEOCODING TEST")
    print("=====================")
    
    # Check if API key is set
    if not os.getenv("MAPBOX_ACCESS_TOKEN"):
        print("ERROR: Please set the MAPBOX_ACCESS_TOKEN environment variable")
        print("Example: export MAPBOX_ACCESS_TOKEN=your_mapbox_access_token")
        exit(1)
    
    # Run tests
    test_addresses() 