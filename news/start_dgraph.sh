#!/bin/bash

echo "🚀 Starting News Knowledge Graph Dgraph Services"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install docker-compose and try again."
    exit 1
fi

# Check if the schema file exists
if [ ! -f "schema.dql" ]; then
    echo "❌ schema.dql not found. Please ensure you're in the correct directory."
    exit 1
fi

echo "✅ Docker environment ready"
echo "📋 Starting Dgraph services..."

# Start the services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check Dgraph health
echo "🔍 Checking Dgraph health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Dgraph is healthy and responding"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts: Dgraph not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Dgraph failed to start within expected time"
    echo "📋 Checking logs..."
    docker-compose logs dgraph
    exit 1
fi

# Check Ratel health
echo "🔍 Checking Ratel health..."
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8001 > /dev/null 2>&1; then
        echo "✅ Ratel is healthy and responding"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts: Ratel not ready yet..."
        sleep 3
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "⚠️  Ratel may not be ready yet, but Dgraph is running"
fi

echo ""
echo "🎉 Dgraph services started successfully!"
echo ""
echo "📊 Service Status:"
echo "   • Dgraph Alpha: http://localhost:8080"
echo "   • Dgraph GraphQL: http://localhost:8000"
echo "   • Ratel (Admin UI): http://localhost:8001"
echo ""
echo "🔧 Next steps:"
echo "   1. Open Ratel at http://localhost:8001 to manage your graph"
echo "   2. Update the schema if needed"
echo "   3. Run: make run-import to import news data"
echo "   4. Run: make run-embeddings to generate AI embeddings"
echo ""
echo "💡 Useful commands:"
echo "   • make status        - Check service status"
echo "   • make logs          - View service logs"
echo "   • make stop-dgraph   - Stop services"
echo "   • make start-dgraph  - Start services"
echo ""
echo "🔍 For more help, see README.md"
