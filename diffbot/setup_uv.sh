#!/bin/bash

# Diffbot Knowledge Graph to Neo4j Import - Setup Script
# This script sets up the development environment using uv

set -e  # Exit on any error

echo "🚀 Setting up Diffbot Knowledge Graph to Neo4j Import"
echo "======================================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv found: $(uv --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -e .

# Copy configuration example if needed
if [ ! -f "config.env" ]; then
    echo "📝 Creating config.env from example..."
    cp config.env.example config.env
    echo "✅ config.env created"
else
    echo "⚠️  config.env already exists, skipping..."
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x setup_uv.sh
[ -f "start_neo4j.sh" ] && chmod +x start_neo4j.sh

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.env with your Diffbot API token and Neo4j settings"
echo "2. Start Neo4j: make start-neo4j"
echo "3. Run import: make run-import"
echo ""
echo "For help: make help"