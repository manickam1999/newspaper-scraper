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

# Setup Chrome profile directory with correct permissions
setup_chrome_profile() {
    log_message "Setting up Chrome profile directory..."
    mkdir -p /home/seluser/chrome-profile
    chown -R 1200:1200 /home/seluser/chrome-profile
    chmod -R 755 /home/seluser/chrome-profile
    log_message "Chrome profile directory setup complete"
}

# Setup log file
setup_logging() {
    log_message "Setting up log file..."
    touch /var/log/cron.log
    chmod 0644 /var/log/cron.log
}

# Install and configure cron
setup_cron() {
    log_message "Updating package list and installing cron and moreutils..."
    apt-get update && apt-get install -y cron moreutils

    log_message "Configuring cron jobs..."
    echo "# Environment setup
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PYTHONPATH=/app
SHELL=/bin/bash

# Scraper jobs
0 4 * * 6 root cd /app && /usr/local/bin/python main.py --mode=edge 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> /var/log/cron.log
15 4 * * * root cd /app && /usr/local/bin/python main.py --mode=star 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> /var/log/cron.log
30 4 * * * root cd /app && /usr/local/bin/python main.py --mode=sun 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> /var/log/cron.log" > /etc/cron.d/scraper
    chmod 0644 /etc/cron.d/scraper
}

# Start cron service
start_services() {
    log_message "Starting cron service..."
    service cron start
}

# Run scrapers sequentially
run_sequential() {
    sleep 20
    log_message "Starting sequential run..."
    
    # Run Star scraper first
    log_message "Running Star scraper..."
    cd /app && /usr/local/bin/python main.py --mode=star 2>&1 | tee -a /var/log/cron.log
    
    # Check if Star scraper completed successfully
    if [ $? -eq 0 ]; then
        log_message "Star scraper completed successfully"
        
        # Run Sun scraper
        log_message "Running Sun scraper..."
        cd /app && /usr/local/bin/python main.py --mode=sun 2>&1 | tee -a /var/log/cron.log
        
        if [ $? -eq 0 ]; then
            log_message "Sun scraper completed successfully"
        else
            log_message "Error: Sun scraper failed"
            exit 1
        fi
    else
        log_message "Error: Star scraper failed"
        exit 1
    fi
    
    log_message "Sequential run completed successfully"
}

# Main execution
main() {
    log_message "Starting setup..."
    setup_logging
    setup_chrome_profile
    # Uncomment below for cron setup
    setup_cron
    start_services
    
    # Run sequential scraping instead
    # run_sequential
    
    log_message "Setup complete. Tailing log file..."
    tail -f /var/log/cron.log
}

# Execute main function
main
