#!/bin/bash

echo "🚀 Starting Dgraph for OSM Import"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if ports are available
if lsof -Pi :7474 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 7474 is already in use. Please stop any services using this port."
    exit 1
fi

if lsof -Pi :7687 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 7687 is already in use. Please stop any services using this port."
    exit 1
fi

echo "✅ Starting Neo4j services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for Neo4j to be ready..."
sleep 15

# Check if Neo4j is healthy
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:7474/browser/ > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    echo "⏳ Attempt $attempt/$max_attempts: Waiting for Neo4j..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Neo4j failed to start within the expected time."
    echo "Check the logs with: docker-compose logs neo4j"
    exit 1
fi

echo ""
echo "🎉 Neo4j is now running!"
echo ""
echo "📊 Access Points:"
echo "   • Browser UI: http://localhost:7474/browser/"
echo "   • Bolt Protocol: bolt://localhost:7687"
echo "   • Username: neo4j"
echo "   • Password: password"
echo ""
echo "📁 Next Steps:"
echo "   1. Install Python dependencies: make install"
echo "   2. Validate OSM data: uvx run test_osm_data.py"
echo "   3. Import OSM data: uvx run osm_import.py"
echo ""
echo "🔍 To view logs: docker-compose logs -f neo4j"
echo "🛑 To stop: docker-compose down"
echo ""
