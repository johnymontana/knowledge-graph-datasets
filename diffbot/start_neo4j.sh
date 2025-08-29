#!/bin/bash

# Start Neo4j for Diffbot Knowledge Graph Import
# This script starts Neo4j using Docker Compose with optimized settings

set -e

echo "🚀 Starting Neo4j for Diffbot Knowledge Graph Import"
echo "===================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in current directory"
    exit 1
fi

# Start Neo4j
echo "🐳 Starting Neo4j container..."
docker-compose up -d

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
sleep 5

# Check Neo4j health
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Neo4j did not start within expected time"
    echo "   Check logs: docker-compose logs neo4j"
    exit 1
fi

echo ""
echo "🎉 Neo4j is running successfully!"
echo ""
echo "Access Neo4j:"
echo "  Browser: http://localhost:7474"
echo "  Username: neo4j"
echo "  Password: password"
echo ""
echo "Connection details:"
echo "  URI: bolt://localhost:7687"
echo "  Database: neo4j"
echo ""
echo "To stop Neo4j: docker-compose down"
echo "To view logs: docker-compose logs neo4j"