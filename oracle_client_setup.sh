#!/bin/bash

# Variables
ORACLE_DIR="/home/ubuntu/oracle"
INSTANT_CLIENT_DIR="${ORACLE_DIR}/instantclient"
INSTANT_CLIENT_ZIP_URL="https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linuxx64.zip"
ZIP_FILE_NAME="instantclient-basic-linuxx64.zip"

# Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

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

# Update and install prerequisites
log "Installing dependencies, and tools for Oracle Instant Client libs..."
if sudo apt install -y libaio1 unzip wget; then
  success "Dependencies installed successfully."
else
  error "Failed to install dependencies."
  exit 1
fi

# Create installation directory if it doesn't exist
log "Creating Oracle directory at ${ORACLE_DIR}..."
sudo mkdir -p $ORACLE_DIR && success "Directory created."
cd $ORACLE_DIR

# Download the Instant Client ZIP file
log "Downloading Oracle Instant Client from ${INSTANT_CLIENT_ZIP_URL}..."
if sudo wget "$INSTANT_CLIENT_ZIP_URL" -O $ZIP_FILE_NAME; then
    success "Downloaded Instant Client ZIP file."
else
    error "Failed to download the ZIP file."
    exit 1
fi

# Unzip the Instant Client package
log "Unzipping Instant Client..."
if sudo unzip -oq $ZIP_FILE_NAME -d $ORACLE_DIR; then
    success "Unzipped Instant Client."
    sudo rm -f $ZIP_FILE_NAME
    sudo mv ${ORACLE_DIR}/instantclient* ${INSTANT_CLIENT_DIR}
else
    error "Failed to unzip Instant Client."
    exit 1
fi

# Set up environment variables
log "Updating environment variables..."
echo "export LD_LIBRARY_PATH=${INSTANT_CLIENT_DIR}:\$LD_LIBRARY_PATH" | sudo tee -a ${HOME}/.bashrc
echo "export ORACLE_HOME=${INSTANT_CLIENT_DIR}" | sudo tee -a ${HOME}/.bashrc
echo "export PATH=${INSTANT_CLIENT_DIR}:\$PATH" | sudo tee -a ${HOME}/.bashrc

# Clean up downloaded ZIP file
log "Cleaning up..."

# Final message
success "Oracle Instant Client setup is complete!"
log "Make sure to source ~/.bashrc before proceeding, to setup the env variables correctly"
