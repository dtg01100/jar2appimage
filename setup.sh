#!/bin/bash

# jar2appimage build script
set -e

# Install dependencies if needed
install_dependencies() {
    echo "Installing dependencies..."
    
    # Check if we're on a Debian-based system
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y default-jre wget curl
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y java-17-openjdk wget curl
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --needed jre-openjdk wget curl
    else
        echo "Warning: Could not detect package manager. Please install Java, and AppImageKit manually."
    fi
}

# Download AppImageKit if not present
download_appimagetool() {
    if ! command -v appimagetool &> /dev/null; then
        echo "Downloading appimagetool..."
        ARCH=$(uname -m)
        wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
        chmod +x "appimagetool-${ARCH}.AppImage"
        sudo mv "appimagetool-${ARCH}.AppImage" /usr/local/bin/appimagetool
    fi
}

# Setup Python environment using uv
setup_python_env() {
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    echo "Setting up Python environment with uv..."
    
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies using uv..."
        uv pip install -r requirements.txt
    fi
}

# Main setup
main() {
    echo "Setting up jar2appimage development environment..."
    
    install_dependencies
    download_appimagetool
    setup_python_env
    
    echo "Setup complete!"
    echo "Usage: uv run jar2appimage.py <your-app.jar>"
}

main "$@"