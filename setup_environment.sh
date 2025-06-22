#!/bin/bash

# Grimperium v2 - Environment Setup Script
# This script sets up a complete development environment for Grimperium on Debian-based Linux systems

set -e  # Exit on any error

echo "🧪 Grimperium v2 - Environment Setup"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on Debian-based system
if ! command -v apt &> /dev/null; then
    print_error "This script is designed for Debian-based systems (Ubuntu, Linux Mint, etc.)"
    print_error "Please install dependencies manually or adapt this script for your system."
    exit 1
fi

print_info "Detected Debian-based system. Proceeding with setup..."
echo

# Step 1: Update package lists
echo "📦 Updating package lists..."
if sudo apt update; then
    print_status "Package lists updated successfully"
else
    print_error "Failed to update package lists"
    exit 1
fi
echo

# Step 2: Install system dependencies
echo "🔧 Installing system dependencies..."
SYSTEM_DEPS="wget unzip curl build-essential libomp5 libomp-dev"

if sudo apt install -y $SYSTEM_DEPS; then
    print_status "System dependencies installed successfully"
else
    print_error "Failed to install system dependencies"
    exit 1
fi
echo

# Step 3: Check if Miniconda is already installed
if command -v conda &> /dev/null; then
    print_warning "Conda is already installed. Skipping Miniconda installation."
    CONDA_INSTALLED=true
else
    CONDA_INSTALLED=false
fi

# Step 4: Download and install Miniconda (if not already installed)
if [ "$CONDA_INSTALLED" = false ]; then
    echo "🐍 Installing Miniconda..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    elif [ "$ARCH" = "aarch64" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
    else
        print_error "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    # Download Miniconda installer
    MINICONDA_INSTALLER="/tmp/miniconda_installer.sh"
    if wget -O "$MINICONDA_INSTALLER" "$MINICONDA_URL"; then
        print_status "Miniconda installer downloaded"
    else
        print_error "Failed to download Miniconda installer"
        exit 1
    fi
    
    # Install Miniconda silently
    if bash "$MINICONDA_INSTALLER" -b -p "$HOME/miniconda3"; then
        print_status "Miniconda installed successfully"
        rm "$MINICONDA_INSTALLER"
    else
        print_error "Failed to install Miniconda"
        exit 1
    fi
    
    # Initialize conda for bash
    echo "🔧 Initializing Conda for bash..."
    if "$HOME/miniconda3/bin/conda" init bash; then
        print_status "Conda initialized for bash"
    else
        print_error "Failed to initialize Conda"
        exit 1
    fi
    
    echo
    print_warning "IMPORTANT: Please close and reopen your terminal (or run 'source ~/.bashrc')"
    print_warning "to activate Conda before proceeding with the next steps."
    echo
else
    print_status "Using existing Conda installation"
    echo
fi

# Step 5: Optional Conda environment setup (commented by default)
echo "🌍 Optional: Conda Environment Setup"
echo "=====================================  "
echo "# The following commands can be used to create the Grimperium environment:"
echo "# "
echo "# conda create -n grimperium python=3.9 -y"
echo "# conda activate grimperium"
echo "# pip install pandas typer rich pydantic pyyaml requests"
echo "# conda install -c conda-forge openbabel crest -y"
echo "# "
echo "# To enable this automatically, uncomment the lines below in this script:"
echo

# Uncomment the following lines to automatically create the Conda environment:
# echo "🌍 Creating Grimperium Conda environment..."
# if source "$HOME/miniconda3/bin/activate" && conda create -n grimperium python=3.9 -y; then
#     print_status "Grimperium environment created"
# else
#     print_error "Failed to create Grimperium environment"
#     exit 1
# fi
# 
# echo "📦 Installing Python packages..."
# if conda activate grimperium && pip install pandas typer rich pydantic pyyaml requests; then
#     print_status "Python packages installed"
# else
#     print_error "Failed to install Python packages"
#     exit 1
# fi
# 
# echo "🧪 Installing chemistry software..."
# if conda install -c conda-forge openbabel crest -y; then
#     print_status "Chemistry software installed"
# else
#     print_error "Failed to install chemistry software"
#     exit 1
# fi

# Step 6: Final instructions
echo
echo "🎉 Setup completed successfully!"
echo "================================"
echo
print_info "Next steps:"
echo "1. Close and reopen your terminal (or run 'source ~/.bashrc')"
echo "2. Create the Grimperium environment:"
echo "   conda create -n grimperium python=3.9 -y"
echo "3. Activate the environment:"
echo "   conda activate grimperium"
echo "4. Install Python dependencies:"
echo "   pip install pandas typer rich pydantic pyyaml requests"
echo "5. Install chemistry software:"
echo "   conda install -c conda-forge openbabel crest -y"
echo "6. Install MOPAC separately (follow the official MOPAC installation guide)"
echo "7. Test the installation:"
echo "   python main.py info"
echo
print_status "Environment setup script completed!"