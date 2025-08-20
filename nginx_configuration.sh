#!/bin/bash

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
    echo -e "${RED}[ERROR]${NC} $1";
    exit 1
}

# get server ip
SERVER_IP=$(curl -s ifconfig.me)
if [ -z "$SERVER_IP" ]; then
  error "Failed to get server IP address. Please check your network connection."
fi

# make sure ufw is active and running
if ! sudo ufw status | grep -q "Status: active"; then
  # enable ufw
  log "Enabling ufw..."
  sudo ufw enable || error "Failed to enable ufw. Check your firewall settings manually if needed."
fi
success "ufw enabled successfully."

# Nginx installation
log "Installing Nginx..."
sudo apt install -y nginx || error "Failed to install Nginx."

sudo ufw allow 'Nginx Full' || error "Failed to add Nginx App. Check your firewall settings manually if needed."

# Enable Nginx to start on boot
log "Enabling Nginx to start on boot..."
if sudo systemctl enable nginx; then
  success "Nginx enabled to start on boot."
else
  error "Failed to enable Nginx on boot."
fi

# Start Nginx service
log "Starting Nginx service..."
if sudo systemctl start nginx; then
  success "Nginx service started."
else
  error "Failed to start Nginx service."
fi

# Check Nginx status
log "Checking Nginx status..."
if sudo systemctl status nginx | grep -q "active (running)"; then
  success "Nginx is running."
else
  warn "Nginx is installed but not running. You may need to troubleshoot."
fi

# create a configuration file for the application server
log "Creating a configuration file for the application server..."
echo "server{
    server_name ${SERVER_IP};

    location / {
           include proxy_params;
           proxy_pass http://127.0.0.1:8000;
       }
}
" | sudo tee /etc/nginx/sites-available/app_server;
sudo ln -sf /etc/nginx/sites-available/app_server /etc/nginx/sites-enabled/

# Test Nginx configuration
log "Testing Nginx configuration..."
if sudo nginx -t; then
  success "Nginx configuration test passed."
else
  error "Nginx configuration test failed. Check the configuration files."
fi

# Restart Nginx service
log "Restarting Nginx service to apply changes..."
if sudo systemctl restart nginx; then
  success "Nginx service restarted."
else
  error "Failed to restart Nginx service."
fi

# Final message
success "Nginx installation and configuration are complete! You can access the server by navigating to the server's IP address in a browser. If your app is not running yet, you should get a 502 Bad Gateway error."

# reboot the server
log "Rebooting the server..."
sudo reboot