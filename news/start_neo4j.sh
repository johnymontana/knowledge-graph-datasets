#!/bin/bash

# Start Neo4j Services Script
# This script starts Neo4j using Docker Compose and sets up the schema

set -e

echo "🚀 Starting Neo4j services..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting Neo4j container..."
docker-compose up -d

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting 2 seconds..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start within expected time"
    echo "📋 Checking logs..."
    docker-compose logs neo4j
    exit 1
fi

# Setup schema if cypher-shell is available
echo "🏗️  Setting up Neo4j schema..."
if command -v cypher-shell &> /dev/null; then
    echo "   Using cypher-shell to setup schema..."
    if [ -f schema.cypher ]; then
        cypher-shell -u neo4j -p password -f schema.cypher
        echo "✅ Schema setup complete!"
    else
        echo "⚠️  schema.cypher file not found, skipping schema setup"
    fi
else
    echo "⚠️  cypher-shell not available, schema setup skipped"
    echo "   You can setup the schema manually using Neo4j Browser at http://localhost:7474"
fi

echo ""
echo "🎉 Neo4j services are running!"
echo ""
echo "📋 Service Information:"
echo "   Neo4j Browser: http://localhost:7474"
echo "   Bolt Protocol: bolt://localhost:7687"
echo "   Username: neo4j"
echo "   Password: password"
echo ""
echo "🔧 Next Steps:"
echo "   1. Configure your API keys in config.env"
echo "   2. Run: make run-validate"
echo "   3. Import data: make run-import"
echo "   4. Generate embeddings: make run-embeddings"
echo ""
echo "🛑 To stop services: make stop-neo4j"