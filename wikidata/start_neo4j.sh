#!/bin/bash
# Start Neo4j database using Docker Compose

set -e

echo "🚀 Starting Neo4j database..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Neo4j with Docker Compose
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
    echo "✅ Neo4j started with Docker Compose"
else
    echo "⚠️  No docker-compose.yml found, starting with docker run..."
    
    # Start Neo4j container with default settings
    docker run -d \
        --name neo4j-wikidata \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/password \
        -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
        -e NEO4J_apoc_export_file_enabled=true \
        -e NEO4J_apoc_import_file_enabled=true \
        -e NEO4J_apoc_import_file_use__neo4j__config=true \
        -v neo4j-wikidata-data:/data \
        -v neo4j-wikidata-logs:/logs \
        neo4j:5.15
    
    echo "✅ Neo4j container started"
fi

echo ""
echo "🌐 Neo4j is now starting..."
echo "📱 Web interface: http://localhost:7474"
echo "🔌 Bolt connection: bolt://localhost:7687"
echo "🔑 Default credentials: neo4j/password"
echo ""
echo "⏳ Waiting for Neo4j to be ready..."

# Wait for Neo4j to be ready
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec neo4j-wikidata cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    echo "⏳ Waiting... (attempt $((attempt + 1))/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start within expected time"
    echo "🔍 Check logs: docker logs neo4j-wikidata"
    exit 1
fi

echo ""
echo "🎉 Neo4j is ready for Wikidata import!"
echo ""
echo "Next steps:"
echo "1. Configure connection: edit config.env"
echo "2. Test connection: make test-connection"
echo "3. Run import: make run-import"