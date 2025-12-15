#!/bin/bash

# Modern installation script using uv
set -e

echo "🚀 Installing jar2appimage with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install the package in development mode
echo "🔧 Installing jar2appimage..."
uv pip install -e .

# Verify installation
if command -v jar2appimage &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "🎯 Usage examples:"
    echo "  jar2appimage myapp.jar"
    echo "  jar2appimage myapp.jar -n 'My App' -o ~/Applications"
    echo "  jar2appimage myapp.jar --java-version 21 --verbose"
    echo ""
    echo "📚 For more help: jar2appimage --help"
else
    echo "❌ Installation failed. Please check the output above."
    exit 1
fi