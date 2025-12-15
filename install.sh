#!/bin/bash

# Modern installation script using uv
set -e

echo "🚀 Installing jar2appimage with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv tool..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Verify uv installation
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv tool"
        exit 1
    fi
    echo "✅ uv tool installed successfully"
fi

# Install jar2appimage as a tool
echo "🔧 Installing jar2appimage..."
uv tool install .

# Verify installation
if command -v jar2appimage &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "🎯 Usage examples:"
    echo "  jar2appimage myapp.jar"
    echo "  jar2appimage myapp.jar --output ~/Applications"
    echo ""
    echo "📚 For more help: jar2appimage --help"
else
    echo "❌ Installation failed. jar2appimage command not found."
    exit 1
fi
