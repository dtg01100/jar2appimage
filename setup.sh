#!/bin/bash

# jar2appimage build script
set -e

# Install dependencies if needed
install_dependencies() {
    echo "Installing dependencies..."
    
    # Check if we're on a Debian-based system
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip default-jre wget curl
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip java-17-openjdk wget curl
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --needed python python-pip jre-openjdk wget curl
    else
        echo "Warning: Could not detect package manager. Please install Python 3, Java, and AppImageKit manually."
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

# Create virtual environment and install Python dependencies
setup_python_env() {
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
}

# Main setup
main() {
    echo "Setting up jar2appimage development environment..."
    
    install_dependencies
    download_appimagetool
    setup_python_env
    
    echo "Setup complete!"
    echo "Usage: source venv/bin/activate && python3 jar2appimage.py <your-app.jar>"
}

main "$@"