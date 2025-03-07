from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
import os
import requests
from progress_tracker_service import process_progress_data
from shelter_service import get_shelter_service

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger('la_fires_api')
logger.setLevel(logging.INFO)

# Create file handler for logging to a file
file_handler = RotatingFileHandler('logs/la_fires_api.log', maxBytes=10485760, backupCount=10)
file_handler.setLevel(logging.INFO)

# Create console handler for logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)

# Stay Healthy Endpoints
@app.route('/api/stayhealthy/aqi', methods=['GET'])
def get_air_quality():
    logger.info("Endpoint hit: /api/stayhealthy/aqi")
    return jsonify({"message": "Air Quality Index endpoint"})

def geocode_address(address: str):
    """
    Convert address to lat/lon coordinates using Mapbox Geocoding API
    
    Args:
        address: The address string to geocode
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding failed
    """
    # Get Mapbox API key from environment
    mapbox_token = os.getenv("MAPBOX_ACCESS_TOKEN")
    if not mapbox_token:
        logger.error("MAPBOX_ACCESS_TOKEN environment variable not set")
        return None
        
    try:
        # URL encode the address
        encoded_address = requests.utils.quote(address)
        
        # Construct Mapbox Geocoding API URL
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"
        params = {
            "access_token": mapbox_token,
            "limit": 1,  # We only need the top result
            "country": "US"  # Limit to US results
        }
        
        # Make request to Mapbox
        logger.info(f"Geocoding address: {address}")
        response = requests.get(url, params=params)
        
        # Check response
        if response.status_code != 200:
            logger.error(f"Mapbox API error: {response.status_code} - {response.text}")
            return None
            
        # Parse response
        data = response.json()
        
        # Check if we got features back
        if not data.get("features") or len(data["features"]) == 0:
            logger.warning(f"No geocoding results found for address: {address}")
            return None
            
        # Get coordinates [longitude, latitude]
        coordinates = data["features"][0]["center"]
        
        # Return as (latitude, longitude) - note the order reversal from Mapbox's format
        return (coordinates[1], coordinates[0])
        
    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}")
        return None

@app.route('/api/stayhealthy/getshelter', methods=['GET'])
def get_shelter():
    logger.info("Endpoint hit: /api/stayhealthy/getshelter")
    
    try:
        # Check if direct lat/lon coordinates are provided
        direct_lat = request.args.get('lat')
        direct_lon = request.args.get('lon')
        
        # Get optional radius parameter (default 50km)
        try:
            distance = float(request.args.get('distance', 10.0))
        except ValueError:
            distance = 50.0
        
        # If direct coordinates are provided, use them
        if direct_lat and direct_lon:
            try:
                lat = float(direct_lat)
                lon = float(direct_lon)
                logger.info(f"Using direct coordinates: ({lat}, {lon})")
                
                # Initialize shelter service
                shelter_service = get_shelter_service()
                
                # Query for nearby shelters using the provided coordinates
                shelters = shelter_service.get_shelters_by_location(lat, lon, distance_km=distance)
                
                # Return results with coordinates
                return jsonify({
                    "success": True, 
                    "coordinates": {"lat": lat, "lon": lon},
                    "search_radius_km": distance,
                    "shelters": shelters,
                    "shelter_count": len(shelters),
                    "source": "direct_coordinates"
                })
            except ValueError:
                return jsonify({
                    "success": False, 
                    "error": "Invalid latitude or longitude values"
                }), 400
        
        # Otherwise, use address geocoding
        address = request.args.get('address')
        
        if not address:
            return jsonify({
                "success": False, 
                "error": "Either address or lat/lon parameters are required"
            }), 400
        
        # Add "Los Angeles, CA" if it doesn't contain city/state info
        address_lower = address.lower()
        if "los angeles" not in address_lower and "la" not in address_lower:
            if "ca" not in address_lower and "california" not in address_lower:
                # Neither city nor state found, add both
                address = f"{address}, Los Angeles, CA"
            else:
                # State found but not city, add city
                address = f"{address}, Los Angeles"
        elif "ca" not in address_lower and "california" not in address_lower:
            # City found but not state, add state
            address = f"{address}, CA"
            
        logger.info(f"Normalized address: {address}")
        
        # Geocode the address
        coordinates = geocode_address(address)
        
        if not coordinates:
            return jsonify({
                "success": False, 
                "error": "Could not geocode the provided address"
            }), 400
            
        # Get lat/lon from coordinates
        lat, lon = coordinates
        logger.info(f"Geocoded coordinates: ({lat}, {lon})")
        
        # Initialize shelter service
        shelter_service = get_shelter_service()
        
        # Query for nearby shelters using the geocoded coordinates
        shelters = shelter_service.get_shelters_by_location(lat, lon, distance_km=distance)
        
        # Return results with original address and coordinates
        return jsonify({
            "success": True, 
            "address": address,
            "coordinates": {"lat": lat, "lon": lon},
            "search_radius_km": distance,
            "shelters": shelters,
            "shelter_count": len(shelters)
        })
        
    except Exception as e:
        error_msg = f"Error retrieving shelter data: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

# Check Progress Endpoint
@app.route('/api/checkprogress', methods=['GET'])
def check_progress():
    logger.info("Endpoint hit: /api/checkprogress")
    progress_data = process_progress_data()
    return jsonify(progress_data)

# Deadlines Endpoint
@app.route('/api/deadlines', methods=['GET'])
def get_deadlines():
    logger.info("Endpoint hit: /api/deadlines")
    return jsonify({"message": "Upcoming Deadlines endpoint"})

# Missing Person/Pet Endpoints
@app.route('/api/missing', methods=['GET', 'POST'])
def missing():
    if request.method == 'POST':
        logger.info("Endpoint hit: /api/missing (POST - Report Missing)")
        return jsonify({"message": "Report Missing Person/Pet endpoint"})
    else:
        logger.info("Endpoint hit: /api/missing (GET - Query Missing)")
        return jsonify({"message": "Query Missing Person/Pet endpoint"})

@app.route('/api/debug/shelters', methods=['GET'])
def debug_shelters():
    """Debug endpoint to list all shelters with their coordinates"""
    logger.info("Endpoint hit: /api/debug/shelters")
    
    try:
        # Initialize shelter service
        shelter_service = get_shelter_service()
        
        # Get all shelters
        all_shelters = shelter_service.get_all_shelters()
        
        # Return first 10 shelters with their coordinates
        sample_shelters = all_shelters[:10]
        
        # Count shelters with valid coordinates
        valid_coords = sum(1 for s in all_shelters if s.get('lat') != 0 and s.get('lon') != 0)
        
        return jsonify({
            "success": True,
            "total_shelters": len(all_shelters),
            "shelters_with_valid_coords": valid_coords,
            "sample_shelters": sample_shelters,
            "csv_format": "address,bookinglink,phonenumber(in lat column),latitude(in lon column),longitude(in phonenumber column),notes"
        })
        
    except Exception as e:
        error_msg = f"Error retrieving shelter data: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/api/debug/nearest-shelters', methods=['GET'])
def debug_nearest_shelters():
    """Debug endpoint to find the nearest shelters to specific coordinates"""
    logger.info("Endpoint hit: /api/debug/nearest-shelters")
    
    try:
        # Use Van Nuys / Ventura coordinate for testing
        test_lat = 34.18466
        test_lon = -118.44873
        
        # Get optional radius parameter (default 100km for wide search)
        try:
            distance = float(request.args.get('distance', 100.0))
        except ValueError:
            distance = 100.0
            
        logger.info(f"Testing with coordinates: ({test_lat}, {test_lon}) and radius {distance}km")
        
        # Initialize shelter service
        shelter_service = get_shelter_service()
        
        # Get all shelters and calculate distances
        all_shelters = shelter_service.get_all_shelters()
        
        # Calculate distance for each shelter
        for shelter in all_shelters:
            shelter_lat = shelter.get('lat')
            shelter_lon = shelter.get('lon')
            if shelter_lat is not None and shelter_lon is not None:
                distance_km = shelter_service._haversine(test_lat, test_lon, shelter_lat, shelter_lon)
                shelter['distance_km'] = round(distance_km, 2)
        
        # Sort by distance
        all_shelters.sort(key=lambda x: x.get('distance_km', float('inf')))
        
        # Get shelters within the specified radius
        nearby_shelters = [s for s in all_shelters if s.get('distance_km', float('inf')) <= distance]
        
        # Return the closest 10 shelters
        closest_shelters = all_shelters[:10]
        
        return jsonify({
            "success": True,
            "coordinates": {"lat": test_lat, "lon": test_lon},
            "search_radius_km": distance,
            "shelters_within_radius": len(nearby_shelters),
            "closest_shelters": closest_shelters
        })
        
    except Exception as e:
        error_msg = f"Error retrieving shelter data: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

if __name__ == '__main__':
    logger.info("Starting LA Fires API server")
    app.run(debug=True, port=6000) 