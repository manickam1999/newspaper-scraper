#!/bin/bash

# Add cron job
echo "0 6 * * * cd /app && /usr/local/bin/python main.py --mode star >> /var/log/cron.log 2>&1" > /etc/cron.d/star-job
chmod 0644 /etc/cron.d/star-job

# Apply cron job
crontab /etc/cron.d/star-job

# Start cron daemon
service cron start

echo "Star mode service is now live!"
echo "Scheduled to run daily at 6:00 AM (Asia/Kuala_Lumpur)"
echo "Watching logs..."

# Keep container running
tail -f /var/log/cron.log
