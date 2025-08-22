#!/bin/bash

# Start Neo4j using Docker Compose
# This script starts a Neo4j instance for GTFS data import and querying

echo "🚀 Starting Neo4j for GTFS project..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create data directories if they don't exist
mkdir -p data

# Start Neo4j
echo "📦 Starting Neo4j container..."
docker-compose -f docker-compose-neo4j.yml up -d

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
sleep 10

# Check if Neo4j is healthy
echo "🔍 Checking Neo4j health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose -f docker-compose-neo4j.yml exec -T neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Neo4j failed to start after $max_attempts attempts"
        echo "📋 Check logs with: docker-compose -f docker-compose-neo4j.yml logs neo4j"
        exit 1
    fi
    
    echo "⏳ Attempt $attempt/$max_attempts - Neo4j not ready yet, waiting..."
    sleep 5
    ((attempt++))
done

echo ""
echo "🎉 Neo4j is now running!"
echo "🌐 Neo4j Browser: http://localhost:7474"
echo "🔗 Bolt endpoint: bolt://localhost:7687"
echo "👤 Username: neo4j"
echo "🔑 Password: password"
echo ""
echo "📊 To import GTFS data, run:"
echo "   python gtfs_import_neo4j.py"
echo ""
echo "🔍 To run sample queries, run:"
echo "   python sample_queries_neo4j.py"
echo ""
echo "🛑 To stop Neo4j, run:"
echo "   docker-compose -f docker-compose-neo4j.yml down"