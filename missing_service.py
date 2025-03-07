import logging
import weaviate
import os
import uuid
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import datetime

# Set up logging for this module
logger = logging.getLogger('la_fires_api.missing')

# Constants
MISSING_CLASS_NAME = "Missing"
MODEL_NAME = "all-MiniLM-L6-v2"  # Smaller but efficient model

class MissingService:
    """Service for managing missing person/pet entries with vector search"""
    
    def __init__(self, weaviate_url: str = None):
        """
        Initialize the Missing service
        
        Args:
            weaviate_url: URL of the Weaviate instance (default: http://localhost:8080)
        """
        self.weaviate_url = weaviate_url or "http://localhost:8080"
        self.client = None
        self.model = None
        
        try:
            # Initialize Weaviate client
            self.client = weaviate.Client(self.weaviate_url)
            logger.info(f"Connected to Weaviate at {self.weaviate_url}")
            
            # Initialize the sentence transformer model
            self.model = SentenceTransformer(MODEL_NAME)
            logger.info(f"Initialized sentence transformer model: {MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize MissingService: {str(e)}")
            raise
    
    def create_schema(self) -> bool:
        """
        Create the missing entries schema in Weaviate if it doesn't exist
        
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
            
            if MISSING_CLASS_NAME in existing_classes:
                logger.info(f"Schema for {MISSING_CLASS_NAME} already exists")
                return True
                
            # Define the missing class schema
            missing_class = {
                "class": MISSING_CLASS_NAME,
                "description": "Information about missing persons or pets",
                "vectorizer": "none",  # We'll provide vectors directly
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The description of the missing person or pet"
                    },
                    {
                        "name": "timestamp",
                        "dataType": ["date"],
                        "description": "When this entry was created"
                    }
                ]
            }
            
            # Create the schema
            self.client.schema.create_class(missing_class)
            logger.info(f"Created schema for {MISSING_CLASS_NAME}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create schema: {str(e)}")
            return False
    
    def vectorize_text(self, text: str) -> List[float]:
        """
        Convert text to a vector representation
        
        Args:
            text: The text to vectorize
            
        Returns:
            Vector representation as a list of floats
        """
        if not self.model:
            logger.error("Sentence transformer model not initialized")
            raise RuntimeError("Sentence transformer model not initialized")
            
        try:
            vector = self.model.encode(text)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Failed to vectorize text: {str(e)}")
            raise
    
    def add_missing_entry(self, content: str) -> str:
        """
        Add a missing person/pet entry to Weaviate
        
        Args:
            content: Description of the missing person/pet
            
        Returns:
            ID of the created object or empty string if failed
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return ""
            
        try:
            # Ensure schema exists
            self.create_schema()
            
            # Vectorize the content
            vector = self.vectorize_text(content)
            
            # Prepare data for Weaviate - use RFC3339 format for timestamp
            # Format example: 2020-01-01T00:00:00Z
            current_time = datetime.datetime.now(datetime.timezone.utc)
            rfc3339_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            data_object = {
                "content": content,
                "timestamp": rfc3339_time
            }
            
            # Add object with vector
            result = self.client.data_object.create(
                data_object=data_object,
                class_name=MISSING_CLASS_NAME,
                vector=vector
            )
            
            logger.info(f"Added missing entry with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add missing entry: {str(e)}")
            return ""
    
    def search_missing_entries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for missing entries similar to the query
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching entries
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return []
            
        try:
            # Vectorize the query
            query_vector = self.vectorize_text(query)
            
            # Perform vector search
            result = (
                self.client.query
                .get(MISSING_CLASS_NAME, ["content", "timestamp"])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit)
                .do()
            )
            
            # Extract results
            entries = []
            if result and "data" in result and "Get" in result["data"] and MISSING_CLASS_NAME in result["data"]["Get"]:
                weaviate_entries = result["data"]["Get"][MISSING_CLASS_NAME]
                
                for entry in weaviate_entries:
                    entries.append({
                        "content": entry.get("content", ""),
                        "timestamp": entry.get("timestamp", "")
                    })
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to search missing entries: {str(e)}")
            return []
    
    def get_all_missing_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all missing entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of all missing entries
        """
        if not self.client:
            logger.error("Weaviate client not initialized")
            return []
            
        try:
            result = (
                self.client.query
                .get(MISSING_CLASS_NAME, ["content", "timestamp"])
                .with_limit(limit)
                .do()
            )
            
            entries = []
            if result and "data" in result and "Get" in result["data"] and MISSING_CLASS_NAME in result["data"]["Get"]:
                weaviate_entries = result["data"]["Get"][MISSING_CLASS_NAME]
                
                for entry in weaviate_entries:
                    entries.append({
                        "content": entry.get("content", ""),
                        "timestamp": entry.get("timestamp", "")
                    })
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get all missing entries: {str(e)}")
            return []

# Global service instance
_missing_service = None

def get_missing_service() -> MissingService:
    """
    Get or create a MissingService instance
    
    Returns:
        MissingService instance
    """
    global _missing_service
    
    if _missing_service is None:
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        _missing_service = MissingService(weaviate_url)
    
    return _missing_service 