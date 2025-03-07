# LA Fires API

A Flask-based Python server hosting endpoints relevant to LA fires.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up Weaviate (required for the shelter service):
   
   Using the utility script:
   ```
   ./run_weaviate_utils.sh start-weaviate
   ```
   
   Or manually:
   ```
   cd weaviate-utils && docker-compose up -d
   ```
   
   This will start both Weaviate and the Weaviate Console (UI) which is accessible at http://localhost:8081
   
   Alternative options:
   ```
   # Using plain Docker
   docker run -d -p 8080:8080 --name weaviate-la-fires semitechnologies/weaviate:1.22.4
   
   # Using Weaviate Cloud Service
   export WEAVIATE_URL=https://your-cluster-url.weaviate.cloud
   ```

5. Set up the Mapbox API key (required for geocoding):
   ```
   export MAPBOX_ACCESS_TOKEN=your_mapbox_access_token
   ```

6. Load shelter data with correct field mappings:
   
   Using the utility script:
   ```
   ./run_weaviate_utils.sh reset-reload
   ```
   
   This will reset the Weaviate schema and reload the shelter data from geocoded.csv with the correct field mappings.

## Running the Application

Start the server:
```
python app.py
```

The server will run at `http://127.0.0.1:6000/`.

## Available Endpoints

### Stay Healthy
- Get Current Air Quality: `GET /api/stayhealthy/aqi`
- Get Shelter Information: `GET /api/stayhealthy/getshelter`
  - Query parameters:
    - `address`: Address string to find shelters near (required if lat/lon not provided)
    - `lat`: Latitude coordinate (optional, used for direct coordinate lookup)
    - `lon`: Longitude coordinate (optional, used with lat for direct coordinate lookup)
    - `distance`: Search radius in kilometers (optional, default: 50km)
  - Examples:
    - Address lookup: `/api/stayhealthy/getshelter?address=123 Main St, Los Angeles, CA&distance=5`
    - Coordinate lookup: `/api/stayhealthy/getshelter?lat=34.052235&lon=-118.243683&distance=10`
  - Notes: 
    - If the address doesn't contain "Los Angeles" and "CA", they will be added automatically
    - The address is geocoded using Mapbox API to convert to coordinates

### Check Progress
- Get Progress Updates: `GET /api/checkprogress`
  - Returns formatted content from the LA Fires tracking webpage

### Upcoming Deadlines
- Get Deadlines: `GET /api/deadlines`

### Missing Person/Pet
- Report Missing: `POST /api/missing`
- Query Missing Reports: `GET /api/missing`

### Debug
- View Shelter Data: `GET /api/debug/shelters`
  - Returns sample shelter data and statistics for debugging

## Weaviate Utilities

The project includes several utilities for working with Weaviate:

- **Start/Stop Weaviate**: 
  ```
  ./run_weaviate_utils.sh start-weaviate
  ./run_weaviate_utils.sh stop-weaviate
  ```

- **Manage Shelter Data**:
  ```
  ./run_weaviate_utils.sh add-shelters     # Add shelters from CSV
  ./run_weaviate_utils.sh reset-reload     # Reset schema and reload with correct mappings
  ./run_weaviate_utils.sh check-shelters   # Check loaded shelter data
  ```

- **Query Shelters**:
  ```
  ./run_weaviate_utils.sh query-shelters
  ```

These utilities are located in the `weaviate-utils` directory and include:
- `add_shelters.py`: Imports shelter data from `geocoded.csv` into Weaviate
- `reset_and_reload.py`: Resets the schema and reloads data with correct field mappings
- `query_shelters.py`: Demonstrates querying shelters from Weaviate
- `check_shelters.py`: Checks if shelters are properly loaded
- `docker-compose.yml`: Configuration for running Weaviate

## Weaviate Schema

The shelter data is stored in Weaviate with the following schema matching the geocoded.csv format:

```
Shelter {
  address: text
  bookingLink: text
  location: geoCoordinates
  phoneNumber: text
  notes: text
}
```

CSV column format:
```
address,bookinglink,lat,lon,phonenumber,notes
```

## Logs

Logs are stored in the `logs` directory and are also printed to the console. 