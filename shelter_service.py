import weaviate
import logging
import os
from typing import Dict, Any, List, Optional
import json
from math import radians, cos, sin, asin, sqrt

# Set up logging for this module
logger = logging.getLogger('la_fires_api.shelter_service')

# Weaviate schema class name for shelters
SHELTER_CLASS_NAME = "Shelter"

class ShelterService:
    """Service class for managing shelter data with Weaviate"""
    
    def __init__(self, weaviate_url: str = None):
        """
        Initialize the shelter service with Weaviate connection
        
        Args:
            weaviate_url: URL to the Weaviate instance, defaults to environment variable
        """
        # Get Weaviate URL from environment variable if not provided
        self.weaviate_url = weaviate_url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.client = None
        
        try:
            # Connect to Weaviate
            self.client = weaviate.Client(self.weaviate_url)
            logger.info(f"Connected to Weaviate at {self.weaviate_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise
    
    def create_schema(self) -> bool:
        """
        Create the shelter schema in Weaviate if it doesn't exist
        
        Returns:
            Boolean indicating success
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return False
            
        try:
            # Check if schema already exists
            schema = self.client.schema.get()
            existing_classes = [c["class"] for c in schema.get("classes", [])]
            
            if SHELTER_CLASS_NAME in existing_classes:
                logger.info(f"Schema for {SHELTER_CLASS_NAME} already exists")
                return True
                
            # Define the shelter class schema
            shelter_class = {
                "class": SHELTER_CLASS_NAME,
                "description": "Information about shelters for LA fires evacuees",
                "properties": [
                    {
                        "name": "hotelName",
                        "dataType": ["text"],
                        "description": "Name of the hotel/shelter"
                    },
                    {
                        "name": "address",
                        "dataType": ["text"],
                        "description": "Full address of the shelter"
                    },
                    {
                        "name": "bookingLink",
                        "dataType": ["text"],
                        "description": "URL for booking or more information"
                    },
                    {
                        "name": "location",
                        "dataType": ["geoCoordinates"],
                        "description": "Geographical coordinates (latitude, longitude)"
                    },
                    {
                        "name": "phoneNumber",
                        "dataType": ["text"],
                        "description": "Contact phone number"
                    },
                    {
                        "name": "notes",
                        "dataType": ["text"],
                        "description": "Additional information about the shelter"
                    }
                ]
            }
            
            # Create the schema
            self.client.schema.create_class(shelter_class)
            logger.info(f"Created schema for {SHELTER_CLASS_NAME}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to create schema: {str(e)}")
            return False
    
    def add_shelter(self, shelter_data: Dict[str, Any]) -> str:
        """
        Add a shelter to the Weaviate database
        
        Args:
            shelter_data: Dictionary containing shelter information
            
        Returns:
            ID of the created object or empty string if failed
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return ""
            
        try:
            # Convert the data format from our API to Weaviate's format
            weaviate_data = {
                "hotelName": shelter_data.get("hotelname", ""),
                "address": shelter_data.get("address", ""),
                "bookingLink": shelter_data.get("bookinglink", ""),
                "location": {
                    "latitude": float(shelter_data.get("lat", 0)),
                    "longitude": float(shelter_data.get("lon", 0))
                },
                "phoneNumber": shelter_data.get("phonenumber", ""),
                "notes": shelter_data.get("notes", "")
            }
            
            # Add the shelter to Weaviate
            result = self.client.data_object.create(
                data_object=weaviate_data,
                class_name=SHELTER_CLASS_NAME
            )
            
            logger.info(f"Added shelter: {shelter_data.get('address')} with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add shelter: {str(e)}")
            return ""
    
    def get_shelters_by_location(self, lat: float, lon: float, distance_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Get shelters near a specific location using geospatial query
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            distance_km: Search radius in kilometers (default: 10km)
            
        Returns:
            List of shelter objects
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return []
            
        try:
            # Log search parameters
            logger.info(f"Searching for shelters near coordinates: ({lat}, {lon}) within {distance_km}km")
            
            # First, check how many shelters we have in total
            count_result = self.client.query.aggregate(SHELTER_CLASS_NAME).with_meta_count().do()
            total_count = 0
            
            if count_result and "data" in count_result and "Aggregate" in count_result["data"] and SHELTER_CLASS_NAME in count_result["data"]["Aggregate"]:
                if count_result["data"]["Aggregate"][SHELTER_CLASS_NAME]:
                    total_count = count_result["data"]["Aggregate"][SHELTER_CLASS_NAME][0]["meta"]["count"]
            
            logger.info(f"Total shelter count in Weaviate before geospatial query: {total_count}")
            
            if total_count == 0:
                logger.warning("No shelters found in the database, please ensure data is loaded")
                return []
            
            # Try a more direct approach - get all shelters and filter by distance in Python
            all_shelters = self.get_all_shelters()
            logger.info(f"Retrieved {len(all_shelters)} shelters for manual distance filtering")
            
            # Print some sample shelters for debugging
            if len(all_shelters) > 0:
                sample_shelter = all_shelters[0]
                logger.info(f"Sample shelter coordinates: ({sample_shelter.get('lat', 'N/A')}, {sample_shelter.get('lon', 'N/A')})")
                logger.info(f"Search coordinates: ({lat}, {lon})")
                
                # Calculate distance for the sample shelter
                sample_distance = self._haversine(lat, lon, sample_shelter.get('lat', 0), sample_shelter.get('lon', 0))
                logger.info(f"Sample shelter distance: {sample_distance:.2f} km")
            
            # Filter shelters by distance using the Haversine formula
            nearby_shelters = []
            for shelter in all_shelters:
                shelter_lat = shelter.get('lat')
                shelter_lon = shelter.get('lon')
                
                if shelter_lat is not None and shelter_lon is not None:
                    # Calculate distance using the haversine formula
                    distance = self._haversine(lat, lon, shelter_lat, shelter_lon)
                    
                    # If within the specified radius, add to results
                    if distance <= distance_km:
                        # Add the calculated distance to the shelter data
                        shelter['distance_km'] = round(distance, 2)
                        nearby_shelters.append(shelter)
            
            # Log the closest shelters even if outside the radius
            if len(all_shelters) > 0 and len(nearby_shelters) == 0:
                # Sort all shelters by distance
                for shelter in all_shelters:
                    shelter_lat = shelter.get('lat')
                    shelter_lon = shelter.get('lon')
                    if shelter_lat is not None and shelter_lon is not None:
                        shelter['distance_km'] = round(self._haversine(lat, lon, shelter_lat, shelter_lon), 2)
                
                closest_shelters = sorted(all_shelters, key=lambda x: x.get('distance_km', float('inf')))[:3]
                logger.info(f"No shelters within {distance_km}km, but here are the closest ones:")
                for i, shelter in enumerate(closest_shelters):
                    logger.info(f"  {i+1}. {shelter.get('address')} - {shelter.get('distance_km')} km away")
            
            # Sort by distance
            nearby_shelters.sort(key=lambda x: x.get('distance_km', float('inf')))
            
            logger.info(f"Found {len(nearby_shelters)} shelters within {distance_km}km using manual distance calculation")
            
            return nearby_shelters
            
        except Exception as e:
            logger.error(f"Failed to query shelters by location: {str(e)}")
            logger.exception("Stack trace:")
            return []
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r
    
    def get_all_shelters(self) -> List[Dict[str, Any]]:
        """
        Get all shelters from the database
        
        Returns:
            List of all shelter objects
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return []
            
        try:
            # First, check how many shelters we have in total
            count_result = self.client.query.aggregate(SHELTER_CLASS_NAME).with_meta_count().do()
            total_count = 0
            
            if count_result and "data" in count_result and "Aggregate" in count_result["data"] and SHELTER_CLASS_NAME in count_result["data"]["Aggregate"]:
                if count_result["data"]["Aggregate"][SHELTER_CLASS_NAME]:
                    total_count = count_result["data"]["Aggregate"][SHELTER_CLASS_NAME][0]["meta"]["count"]
            
            logger.info(f"Total shelter count in Weaviate: {total_count}")
            
            if total_count == 0:
                logger.warning("No shelters found in the database")
                return []
            
            # Now get all shelters with a higher limit
            query = (
                self.client.query
                .get(SHELTER_CLASS_NAME, [
                    "hotelName",
                    "address", 
                    "bookingLink", 
                    "phoneNumber", 
                    "notes", 
                    "location { latitude longitude }"
                ])
                .with_limit(1000)  # Increased limit
            )
            
            result = query.do()
            
            # Process results
            shelters = []
            if result and "data" in result and "Get" in result["data"] and SHELTER_CLASS_NAME in result["data"]["Get"]:
                weaviate_shelters = result["data"]["Get"][SHELTER_CLASS_NAME]
                
                for shelter in weaviate_shelters:
                    # Convert from Weaviate format to our API format
                    location = shelter.get("location", {})
                    shelters.append({
                        "hotelname": shelter.get("hotelName", ""),
                        "address": shelter.get("address", ""),
                        "bookinglink": shelter.get("bookingLink", ""),
                        "lat": location.get("latitude", 0),
                        "lon": location.get("longitude", 0),
                        "phonenumber": shelter.get("phoneNumber", ""),
                        "notes": shelter.get("notes", "")
                    })
            
            logger.info(f"Retrieved {len(shelters)} shelters")
            return shelters
            
        except Exception as e:
            logger.error(f"Failed to query all shelters: {str(e)}")
            return []
            
# Helper function to initialize the service (for use in the API)
def get_shelter_service() -> ShelterService:
    """
    Get or create a shelter service instance
    
    Returns:
        ShelterService instance
    """
    try:
        service = ShelterService()
        # Create schema if it doesn't exist
        service.create_schema()
        return service
    except Exception as e:
        logger.error(f"Failed to initialize shelter service: {str(e)}")
        # Return a non-functional service instance as a fallback
        return ShelterService(weaviate_url=None) 