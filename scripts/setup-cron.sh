#!/bin/bash

# setup-cron.sh
# Purpose: Sets up and configures cron job for the scraper application
# Usage: ./setup-cron.sh
# Author: System Administrator
# Date: March 30, 2024

set -e  # Exit on error

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Setup log file
setup_logging() {
    log_message "Setting up log file..."
    touch /var/log/cron.log
    chmod 0644 /var/log/cron.log
}

# Install and configure cron
setup_cron() {
    log_message "Updating package list and installing cron..."
    apt-get update && apt-get install -y cron

    log_message "Configuring cron jobs..."
    echo "0 4 * * * cd /app && python main.py --mode=edge >> /var/log/cron.log 2>&1
15 4 * * * cd /app && python main.py --mode=star >> /var/log/cron.log 2>&1
30 4 * * * cd /app && python main.py --mode=sun >> /var/log/cron.log 2>&1" > /etc/cron.d/scraper
    chmod 0644 /etc/cron.d/scraper
    crontab /etc/cron.d/scraper
}

# Start cron service
start_services() {
    log_message "Starting cron service..."
    service cron start
}

# Main execution
main() {
    log_message "Starting cron setup..."
    setup_logging
    setup_cron
    start_services
    
    log_message "Setup complete. Tailing log file..."
    tail -f /var/log/cron.log
}

# Execute main function
main
