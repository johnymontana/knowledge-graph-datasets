#!/bin/bash
# Wikidata Neo4j Import Setup Script
# This script sets up the Python environment using uv package manager

set -e  # Exit on any error

echo "🚀 Setting up Wikidata Neo4j import environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv package manager is not installed"
    echo "📦 Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv package manager found"

# Create virtual environment and install dependencies
echo "📦 Installing dependencies with uv..."
uv sync

echo "🔧 Creating example configuration file..."
if [ ! -f "config.env" ]; then
    cp config.env.example config.env
    echo "✅ Created config.env from example"
    echo "📝 Please edit config.env with your Neo4j connection details"
else
    echo "⚠️  config.env already exists, skipping creation"
fi

echo "📁 Creating data directory..."
mkdir -p data

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.env with your Neo4j connection details"
echo "2. Start Neo4j: ./start_neo4j.sh"
echo "3. Run the import: make run-import"
echo "4. Explore with queries: make run-query"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate  # or use: uv run <command>"