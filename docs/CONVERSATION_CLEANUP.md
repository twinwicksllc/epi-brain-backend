# Conversation Cleanup System

This document describes the automatic conversation cleanup system for EPI Brain.

## Overview

The conversation cleanup system automatically removes conversations that haven't been updated for a specified number of days (default: 30 days). This helps maintain database performance and reduces storage costs.

## Components

### 1. Cleanup Service (`app/services/conversation_cleanup.py`)

The core service that handles the cleanup logic:

- **ConversationCleanupService**: Main service class
  - `cleanup_old_conversations()`: Delete conversations older than threshold
  - `count_old_conversations()`: Count conversations that would be deleted
  - `cleanup_conversations_for_user()`: Clean up for specific user
  - `get_cutoff_date()`: Calculate the cutoff date for deletion

### 2. CLI Commands (`app/cli/cleanup_conversations.py`)

Command-line interface for running cleanup:

```bash
# Count old conversations
python -m app.cli.cleanup_conversations count --days 30

# Dry run (show what would be deleted)
python -m app.cli.cleanup_conversations old --days 30 --dry-run

# Actual cleanup
python -m app.cli.cleanup_conversations old --days 30

# Cleanup for specific user
python -m app.cli.cleanup_conversations user --user-id <UUID> --days 30
```

### 3. Admin API Endpoints (`app/api/admin.py`)

API endpoints for triggering cleanup:

- `POST /api/v1/admin/conversations/cleanup` - Run cleanup
- `GET /api/v1/admin/conversations/count-old` - Count old conversations
- `POST /api/v1/admin/conversations/cleanup-user/{user_id}` - Cleanup for specific user

Example API usage:

```bash
# Count old conversations
curl -X GET "https://api.epibrain.com/api/v1/admin/conversations/count-old?days=30" \
  -H "X-Admin-Key: your-admin-key"

# Dry run
curl -X POST "https://api.epibrain.com/api/v1/admin/conversations/cleanup" \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"days_threshold": 30, "dry_run": true, "batch_size": 100}'

# Actual cleanup
curl -X POST "https://api.epibrain.com/api/v1/admin/conversations/cleanup" \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"days_threshold": 30, "dry_run": false, "batch_size": 100}'
```

### 4. Shell Script (`scripts/run_conversation_cleanup.sh`)

Shell script for automated execution via cron:

```bash
# Run with default settings (30 days)
./scripts/run_conversation_cleanup.sh

# Run with custom settings
DAYS_THRESHOLD=60 BATCH_SIZE=200 ./scripts/run_conversation_cleanup.sh
```

## Scheduled Cleanup Setup

### Option 1: Cron Job

Add to crontab (`crontab -e`):

```cron
# Run cleanup daily at 2 AM UTC
0 2 * * * /path/to/epi-brain-backend/scripts/run_conversation_cleanup.sh
```

### Option 2: Systemd Timer

Create `/etc/systemd/system/epi-brain-cleanup.service`:

```ini
[Unit]
Description=EPI Brain Conversation Cleanup
After=network.target

[Service]
Type=oneshot
User=epibrain
WorkingDirectory=/path/to/epi-brain-backend
ExecStart=/path/to/epi-brain-backend/scripts/run_conversation_cleanup.sh
Environment="DAYS_THRESHOLD=30"
```

Create `/etc/systemd/system/epi-brain-cleanup.timer`:

```ini
[Unit]
Description=Run EPI Brain cleanup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
sudo systemctl enable epi-brain-cleanup.timer
sudo systemctl start epi-brain-cleanup.timer
```

### Option 3: Cloud Scheduler (Render/AWS/Google Cloud)

#### Render Cron Jobs
Add to your `render.yaml`:

```yaml
services:
  - type: cron
    name: conversation-cleanup
    schedule: "0 2 * * *"
    command: python -m app.cli.cleanup_conversations old --days 30
    envVars:
      - key: DAYS_THRESHOLD
        value: 30
```

#### AWS EventBridge/CloudWatch Events
Create a scheduled rule that triggers a Lambda function or ECS task to run the cleanup script.

#### Google Cloud Scheduler
Create a job that triggers a Cloud Run service or Cloud Function to execute the cleanup.

## Configuration

The cleanup behavior can be configured via:

- `DAYS_THRESHOLD`: Number of days before conversations are considered old (default: 30)
- `BATCH_SIZE`: Number of conversations to delete per batch (default: 100)
- `dry_run`: If true, only counts what would be deleted (default: false)

## Safety Features

1. **Dry Run Mode**: Always test with `--dry-run` first
2. **Batch Processing**: Deletes in batches to avoid long-running transactions
3. **Cutoff Date**: Uses `updated_at` timestamp, not `created_at`
4. **Cascade Delete**: Messages are automatically deleted when conversations are deleted
5. **Logging**: All operations are logged for audit trail

## Monitoring

Check cleanup logs:

```bash
# View recent cleanup logs
tail -f /var/log/epi-brain/conversation_cleanup.log

# Check for errors
grep -i error /var/log/epi-brain/conversation_cleanup.log
```

## Database Schema

The cleanup relies on the `updated_at` field in the `conversations` table:

```sql
-- View conversations that would be deleted
SELECT id, title, mode, updated_at 
FROM conversations 
WHERE updated_at < NOW() - INTERVAL '30 days'
ORDER BY updated_at ASC;
```

## Backups

Before running cleanup for the first time in production:

1. **Take a database backup**
2. **Run with dry_run=true**
3. **Review the count and affected conversations**
4. **Run a small batch first**
5. **Monitor for any issues**
6. **Scale up to full cleanup**

## Troubleshooting

### Cleanup not running
- Check logs: `tail -f /var/log/epi-brain/conversation_cleanup.log`
- Verify cron/scheduler is running
- Check Python environment and dependencies

### Too many conversations being deleted
- Use `--dry-run` first to verify count
- Adjust `DAYS_THRESHOLD` if needed
- Check `updated_at` timestamps are correct

### Database locks during cleanup
- Reduce `BATCH_SIZE` parameter
- Run during low-traffic hours
- Consider using read replicas for monitoring

## Future Enhancements

- [ ] Add soft delete instead of hard delete
- [ ] Implement retention policies by user tier
- [ ] Add archive to cold storage before deletion
- [ ] Provide user notifications before deletion
- [ ] Add exception lists (never delete certain conversations)
- [ ] Implement gradual cleanup with rate limiting