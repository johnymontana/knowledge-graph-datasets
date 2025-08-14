#!/bin/bash

echo "🚀 Starting Dgraph for OSM Import"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Please stop any services using this port."
    exit 1
fi

if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8080 is already in use. Please stop any services using this port."
    exit 1
fi

echo "✅ Starting Dgraph services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for Dgraph to be ready..."
sleep 10

# Check if Dgraph is healthy
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Dgraph is ready!"
        break
    fi
    
    echo "⏳ Attempt $attempt/$max_attempts: Waiting for Dgraph..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Dgraph failed to start within the expected time."
    echo "Check the logs with: docker-compose logs dgraph"
    exit 1
fi

echo ""
echo "🎉 Dgraph is now running!"
echo ""
echo "📊 Access Points:"
echo "   • GraphQL: http://localhost:8000"
echo "   • HTTP API: http://localhost:8080"
echo "   • Ratel UI: http://localhost:8001"
echo ""
echo "📁 Next Steps:"
echo "   1. Install Python dependencies: make install"
echo "   2. Validate OSM data: uvx run test_osm_data.py"
echo "   3. Import OSM data: uvx run osm_import.py"
echo ""
echo "🔍 To view logs: docker-compose logs -f dgraph"
echo "🛑 To stop: docker-compose down"
echo ""
