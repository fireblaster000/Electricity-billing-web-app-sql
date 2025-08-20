#!/bin/bash

# the script installs python3, pip3, and virtualenv
# Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# Logging Functions
log() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Update package list and install Python, pip
log "Updating package list and installing Python, pip, and virtualenv..."
if sudo apt update && sudo apt install -y python3 python3-pip; then
  success "Python and pip installed successfully."
else
  error "Failed to install Python and pip."
  exit 1
fi

# Install virtualenv
log "Installing virtualenv..."
if sudo pip3 install virtualenv; then
  success "virtualenv installed successfully."
else
  error "Failed to install virtualenv."
  exit 1
fi

# Display Python, pip, and virtualenv versions
log "Python version:"
python3 --version

log "pip version:"
pip3 --version

log "virtualenv version:"
virtualenv --version

# Create project directory and virtual environment
PROJECT_DIR="./application"
VENV_NAME="venv"
VENV_DIR="$PROJECT_DIR/$VENV_NAME"

# check if PROJECT_DIR exists, error out if it doesn't
if [ ! -d "$PROJECT_DIR" ]; then
  error "Project directory $PROJECT_DIR not found. Make sure to put the application files in the correct directory. Expected to find the application files in $PROJECT_DIR."
  exit 1
fi

# check if VENV_DIR exists, error out if it does
if [ -d "$VENV_DIR" ]; then
  error "Virtual environment directory $VENV_DIR already exists. Please remove the existing virtual environment directory before running this script."
  exit 1
fi

log "Creating virtual environment in $VENV_DIR..."
cd $PROJECT_DIR
if virtualenv $VENV_NAME; then
  success "Virtual environment created."
else
  error "Failed to create virtual environment."
  exit 1
fi

# Activate virtual environment
log "Activating virtual environment and installing FastAPI dependencies..."
if source $VENV_NAME/bin/activate; then
  success "Virtual environment activated."
else
  error "Failed to activate virtual environment."
  exit 1
fi

# Install deps
if pip install -r requirements.txt; then
  success "Python modules installed correctly."
else
  error "Failed to install FastAPI dependencies."
  deactivate
  exit 1
fi

# Deactivate virtual environment
deactivate
success "Environment setup is complete! To start using FastAPI, activate the virtual environment with 'source $VENV_DIR/bin/activate'."