#!/bin/bash

echo "🚀 Setting up GTFS Neo4j Importer with uv"
echo "============================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing now..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "✅ uv installed! Please restart your terminal or run: source ~/.zshrc"
        exit 1
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "✅ uv installed! Please restart your terminal or run: source ~/.bashrc"
        exit 1
    else
        echo "❌ Unsupported OS. Please install uv manually:"
        echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

echo "✅ uv is installed (version: $(uv --version))"

# Check if Python 3.8+ is available
python_version=$(uv run python --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $? -ne 0 ]]; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

required_version="3.8"
if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Python $python_version found, but Python 3.8+ is required"
    exit 1
fi

echo "✅ Python $python_version is available"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
uv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -e .

echo ""
echo "🎉 Setup complete! Your environment is ready."
echo ""
echo "📋 Next steps:"
echo "   1. Configure Neo4j connection: cp config.env.neo4j.example config.env"
echo "   2. Edit config.env with your Neo4j connection details"
echo "   3. Validate data: uvx run test_gtfs_data.py"
echo "   4. Import data: uvx run gtfs_import_neo4j.py"
echo "   5. Run queries: uvx run sample_queries_neo4j.py"
echo ""
echo "💡 Useful commands:"
echo "   • make help          - Show all available commands"
echo "   • make config-neo4j  - Show current Neo4j configuration"
echo "   • make config-example - Create example configuration file"
echo "   • uvx run <script>   - Run scripts without activation"
echo "   • uv run python <script> - Run scripts with activated environment"
echo "   • source .venv/bin/activate - Activate virtual environment"
echo "   • deactivate         - Deactivate virtual environment"
echo ""
echo "🔍 For more help, see README_GTFS_Import.md"
