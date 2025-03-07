#!/bin/bash

# Script to run the Weaviate utilities

show_help() {
    echo "Weaviate Utilities Runner"
    echo ""
    echo "Usage:"
    echo "  ./run_weaviate_utils.sh add-shelters     - Import shelters from CSV into Weaviate"
    echo "  ./run_weaviate_utils.sh query-shelters   - Query shelters from Weaviate"
    echo "  ./run_weaviate_utils.sh check-shelters   - Check if shelters are correctly loaded"
    echo "  ./run_weaviate_utils.sh reset-reload     - Reset Weaviate schema and reload data with correct mappings"
    echo "  ./run_weaviate_utils.sh start-weaviate   - Start Weaviate using Docker Compose"
    echo "  ./run_weaviate_utils.sh stop-weaviate    - Stop Weaviate Docker container"
    echo ""
}

# Check if Weaviate Utils directory exists
if [ ! -d "weaviate-utils" ]; then
    echo "Error: weaviate-utils directory not found."
    exit 1
fi

case "$1" in
    add-shelters)
        echo "Importing shelters from CSV into Weaviate..."
        cd weaviate-utils && python add_shelters.py
        ;;
    query-shelters)
        echo "Querying shelters from Weaviate..."
        cd weaviate-utils && python query_shelters.py
        ;;
    check-shelters)
        echo "Checking if shelters are correctly loaded in Weaviate..."
        cd weaviate-utils && python check_shelters.py
        ;;
    reset-reload)
        echo "Resetting Weaviate schema and reloading data with correct field mappings..."
        cd weaviate-utils && python reset_and_reload.py
        ;;
    start-weaviate)
        echo "Starting Weaviate using Docker Compose..."
        cd weaviate-utils && docker-compose up -d
        echo "Weaviate started. API available at http://localhost:8080"
        echo "Weaviate Console available at http://localhost:8081"
        ;;
    stop-weaviate)
        echo "Stopping Weaviate..."
        cd weaviate-utils && docker-compose down
        ;;
    *)
        show_help
        ;;
esac 