#!/bin/bash

# Conversation Cleanup Script
# This script runs the conversation cleanup and logs the results

# Configuration
DAYS_THRESHOLD=${DAYS_THRESHOLD:-30}
BATCH_SIZE=${BATCH_SIZE:-100}
LOG_FILE="/var/log/epi-brain/conversation_cleanup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Create log directory if it doesn't exist
mkdir -p $(dirname "$LOG_FILE")

# Change to the backend directory
cd "$(dirname "$0")/.."

# Log header
echo "========================================" >> "$LOG_FILE"
echo "Conversation Cleanup - $DATE" >> "$LOG_FILE"
echo "Threshold: $DAYS_THRESHOLD days" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

# Run the cleanup
python -m app.cli.cleanup_conversations old \
    --days $DAYS_THRESHOLD \
    --batch-size $BATCH_SIZE \
    2>&1 | tee -a "$LOG_FILE"

# Log completion
echo "----------------------------------------" >> "$LOG_FILE"
echo "Cleanup completed at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"