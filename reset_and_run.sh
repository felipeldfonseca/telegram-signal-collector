#!/bin/bash

echo "🔄 RESETTING ENVIRONMENT AND STARTING DAILY TRADING SYSTEM"
echo "=========================================================="

# Step 1: Kill any existing Python processes
echo "1️⃣  Killing any existing Python processes..."
pkill -f "daily_trading_system.py" 2>/dev/null
pkill -f "main_adaptive.py" 2>/dev/null
pkill -f "collect_historical_data.py" 2>/dev/null
sleep 2

# Step 2: Deactivate any active virtual environment
echo "2️⃣  Deactivating any active virtual environment..."
deactivate 2>/dev/null || true

# Step 3: Clear Python cache
echo "3️⃣  Clearing Python cache..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Step 4: Activate virtual environment
echo "4️⃣  Activating virtual environment..."
source venv/bin/activate

# Step 5: Verify environment
echo "5️⃣  Verifying environment..."
python3 -c "import pytz, telethon, pandas; print('✅ All dependencies available')" || {
    echo "❌ Dependencies missing. Installing..."
    pip install -r requirements.txt
}

# Step 6: Check .env file
echo "6️⃣  Checking .env configuration..."
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Step 7: Start the daily trading system
echo "7️⃣  Starting daily_trading_system.py..."
echo "🚀 SYSTEM STARTING - Press Ctrl+C to stop"
echo "=========================================================="

python3 daily_trading_system.py 