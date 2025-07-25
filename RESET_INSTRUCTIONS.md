# 🔄 MANUAL RESET PROCESS

## Quick Reset Commands (Run these every time):

```bash
# 1. Kill any running processes
pkill -f "daily_trading_system.py"
pkill -f "main_adaptive.py"
pkill -f "collect_historical_data.py"

# 2. Deactivate virtual environment (if active)
deactivate

# 3. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 4. Activate virtual environment
source venv/bin/activate

# 5. Verify dependencies
python3 -c "import pytz, telethon, pandas; print('✅ Ready')"

# 6. Run your script
python3 daily_trading_system.py
```

## Or use the automated script:

```bash
./reset_and_run.sh
```

## What this fixes:
- ✅ Kills stuck processes
- ✅ Clears Python cache conflicts
- ✅ Ensures proper virtual environment activation
- ✅ Verifies all dependencies are available
- ✅ Starts fresh every time

## When to use:
- Before starting any script
- If scripts seem laggy or unresponsive
- If you get import errors
- After system restarts
- When switching between different scripts 