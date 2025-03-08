# Momentum Scheduler

The Momentum module requires daily checks to be run to process various tasks:
- Reset weekly points on Monday
- Reset monthly points on the first of the month
- Check for perfect week completion on Sunday
- Check for perfect month completion on the last day of the month
- Check for leaderboard achievements
- Check for expired streaks

Instead of handling this within the FastAPI application (which could be unreliable in case of application restarts or deployment), we use an external scheduler like systemd timers or cron jobs.

## Available Scripts

### 1. `run_momentum_checks.py`

This script runs all momentum checks at once. It's designed to be run daily by a scheduler.

### 2. `run_specific_momentum_check.py`

This script allows you to run specific types of checks individually. This is useful if you want to schedule different checks at different times or frequencies.

Usage:
```bash
# Run only the leaderboard achievement check
python scripts/run_specific_momentum_check.py --check=leaderboard

# Run only the expired streaks check
python scripts/run_specific_momentum_check.py --check=streaks

# Run weekly checks (perfect week and weekly points reset)
python scripts/run_specific_momentum_check.py --check=weekly

# Run monthly checks (perfect month and monthly points reset)
python scripts/run_specific_momentum_check.py --check=monthly

# Run all checks (same as run_momentum_checks.py)
python scripts/run_specific_momentum_check.py --check=all
```

## Scheduling Options

### 1. Systemd Timer (Recommended for Linux servers)

This is the recommended approach for most Linux servers. The timer will ensure the checks run daily, even if the server reboots.

#### Installation Steps:

1. Edit the systemd service and timer files to match your environment:
   ```bash
   nano systemd/momentum-checks.service
   nano systemd/momentum-checks.timer
   ```
   
   Update the following in the service file:
   - WorkingDirectory: The full path to your planner app
   - ExecStart: The full path to your Python executable and script
   - EnvironmentFile: The path to your environment file (if used)
   - User/Group: The user and group that should run the service

2. Copy the files to the systemd directory:
   ```bash
   sudo cp systemd/momentum-checks.service /etc/systemd/system/
   sudo cp systemd/momentum-checks.timer /etc/systemd/system/
   ```

3. Create the log directory:
   ```bash
   sudo mkdir -p /var/log/planner
   sudo chown www-data:www-data /var/log/planner
   ```

4. Reload systemd, enable and start the timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable momentum-checks.timer
   sudo systemctl start momentum-checks.timer
   ```

5. Verify the timer is active:
   ```bash
   sudo systemctl list-timers | grep momentum
   ```

### 2. Cron Job (Alternative option)

If you prefer using cron or systemd is not available, you can use a cron job instead.

#### Installation Steps:

1. Edit the crontab file to match your environment:
   ```bash
   nano scripts/momentum-crontab
   ```
   
   Update the paths to match your installation.

2. Create the log directory:
   ```bash
   sudo mkdir -p /var/log/planner
   sudo chown www-data:www-data /var/log/planner
   ```

3. Add the cron job to the system:
   ```bash
   # For the current user
   crontab -e
   
   # Or for a specific user (e.g., www-data)
   sudo -u www-data crontab -e
   ```
   
   Add the line from `scripts/momentum-crontab` to the crontab file.

### 3. Advanced Scheduling with Specific Checks

You can also set up more advanced scheduling by running specific checks at different times:

```
# Run weekly checks only on Mondays at 2:00 AM
0 2 * * 1 cd /path/to/your/planner && /path/to/your/venv/bin/python /path/to/your/planner/scripts/run_specific_momentum_check.py --check=weekly >> /var/log/planner/momentum_weekly.log 2>&1

# Run monthly checks only on the 1st day of each month at 2:00 AM
0 2 1 * * cd /path/to/your/planner && /path/to/your/venv/bin/python /path/to/your/planner/scripts/run_specific_momentum_check.py --check=monthly >> /var/log/planner/momentum_monthly.log 2>&1

# Run leaderboard checks only on Sundays at 11:59 PM
59 23 * * 0 cd /path/to/your/planner && /path/to/your/venv/bin/python /path/to/your/planner/scripts/run_specific_momentum_check.py --check=leaderboard >> /var/log/planner/momentum_leaderboard.log 2>&1

# Run streak checks daily at 3:00 AM
0 3 * * * cd /path/to/your/planner && /path/to/your/venv/bin/python /path/to/your/planner/scripts/run_specific_momentum_check.py --check=streaks >> /var/log/planner/momentum_streaks.log 2>&1
```

## Manual Execution

You can also run the checks manually if needed:

```bash
# Activate your virtual environment if needed
source /path/to/venv/bin/activate

# Run all checks
python scripts/run_momentum_checks.py

# Or run a specific check
python scripts/run_specific_momentum_check.py --check=leaderboard
```

## Troubleshooting

### Checking Logs

For systemd:
```bash
sudo journalctl -u momentum-checks.service
cat /var/log/planner/momentum-service.log
```

For cron:
```bash
cat /var/log/planner/momentum_cron.log
```

General checks script logs:
```bash
cat /var/log/planner/momentum_checks.log
cat /var/log/planner/momentum_specific_checks.log
```

### Common Issues

1. **Permissions**: Ensure the service user has permissions to access the script and log directories.
2. **Python Environment**: Make sure the Python path in the service or cron job points to the correct virtual environment.
3. **Timer not running**: Use `systemctl list-timers` to verify your timer is scheduled. 