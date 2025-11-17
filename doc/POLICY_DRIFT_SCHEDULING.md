# Policy Drift Notification Scheduling

The `send_policy_drift_notifications` management command ships with CSV evidence attached and can be executed on a schedule for automated quarterly attestations.

## Windows Task Scheduler

1. Open **Task Scheduler** → **Create Task**.
2. **Triggers** → *New…* → set the cadence (e.g., Monthly, On the 1st, 08:00).
3. **Actions** → *New…* → Action: *Start a program*.
4. Program/script:
   ```
   C:\trae\User-Access-Management-System\venv\Scripts\python.exe
   ```
5. Add arguments:
   ```
   manage.py send_policy_drift_notifications --status-scope=active --stale-threshold=90
   ```
6. Start in:
   ```
   C:\trae\User-Access-Management-System
   ```
7. Optional: append `--system=<ID>` / `--department=<ID>` for scoped notifications, or multiple `--recipient someone@example.com`.

## Linux/macOS Cron

Add to `crontab -e`:

```
0 8 1 * * cd /path/to/User-Access-Management-System && /path/to/venv/bin/python manage.py send_policy_drift_notifications --status-scope=active --stale-threshold=90
```

## Settings

Set default recipients in `user_access_management/settings.py`:

```python
POLICY_DRIFT_NOTIFICATION_RECIPIENTS = [
    "security@hotelgroup.com",
    "audit-team@hotelgroup.com",
]
```

Override recipients ad-hoc with repeated `--recipient` flags.

