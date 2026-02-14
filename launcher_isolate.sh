#!/bin/bash

# Configuration
DEVICE_NAME="HertopiaBot_$$" 
DEVICE_MANAGER_SCRIPT="device_manager.py"
WORK_DIR=$(dirname "$(realpath "$0")")

# 0. Pre-launch Cleanup
echo "Pre-launch cleanup..."
killall -q -9 xdt.exe Heartopia Xephyr || true

# 1. Start Device Manager (Background)
echo "Starting Device Manager..."
LOG_FILE=$(mktemp)
python3 "$WORK_DIR/$DEVICE_MANAGER_SCRIPT" --name "$DEVICE_NAME" > "$LOG_FILE" 2>&1 &
DEVICE_PID=$!

# Wait for device path
DEVICE_PATH=""
MAX_RETRIES=10
COUNT=0
while [ -z "$DEVICE_PATH" ] && [ $COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    if grep -q "DEVICE_PATH=" "$LOG_FILE"; then
        DEVICE_PATH=$(grep "DEVICE_PATH=" "$LOG_FILE" | cut -d'=' -f2 | tr -d '\n\r')
    fi
    COUNT=$((COUNT+1))
done
rm "$LOG_FILE"

if [ -z "$DEVICE_PATH" ]; then
    echo "Error: Failed to create virtual device."
    kill $DEVICE_PID
    exit 1
fi
echo "Device created at: $DEVICE_PATH"

# Cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$BRIDGE_PID" ]; then kill $BRIDGE_PID 2>/dev/null; fi
    if [ ! -z "$WM_PID" ]; then kill $WM_PID 2>/dev/null; fi
    kill $DEVICE_PID 2>/dev/null
    if [ ! -z "$GAME_PID" ]; then kill $GAME_PID 2>/dev/null; fi
    killall -q -9 Xephyr xdt.exe Heartopia 2>/dev/null
}
trap cleanup EXIT INT TERM

# 2. Start Xephyr (Isolated Display)
XEPHYR_DISPLAY=":100"
echo "Starting Xephyr on display $XEPHYR_DISPLAY..."
# We use -glamor for acceleration (might need swrast if glitches occur)
# -host-cursor to prevent mouse lag
Xephyr $XEPHYR_DISPLAY -ac -br -noreset -screen 800x600 -host-cursor -glamor &
XEPHYR_PID=$!
sleep 2

# 3. Start Window Manager (Openbox) inside Xephyr (Essential for focus)
DISPLAY=$XEPHYR_DISPLAY openbox &
WM_PID=$!

# 4. Start Input Bridge targeting Xephyr
export DISPLAY=$XEPHYR_DISPLAY
echo "Starting Input Bridge..."
uv run --with python-xlib input_bridge.py "$DEVICE_PATH" &
BRIDGE_PID=$!

# 5. Launch Game inside Xephyr
PROTON_BIN="/home/daniel/.config/heroic/tools/proton/GE-Proton-latest/proton"
WINE_PREFIX="/home/daniel/Games/Heroic/Prefixes/default/Heartopia"
GAME_EXE="/home/daniel/.local/share/Steam/steamapps/common/Heartopia/xdt.exe"
cd "$(dirname "$GAME_EXE")"

export STEAM_COMPAT_DATA_PATH="$WINE_PREFIX"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="/home/daniel/.local/share/Steam"
export WINEPREFIX="$WINE_PREFIX"

# Try Native Vulkan in Xephyr for better performance (requires modern Xephyr + drivers)
# If this fails/crashes, we can revert to PROTON_USE_WINED3D=1
# export PROTON_USE_WINED3D=1

echo "Launching Heartopia in Isolation (Vulkan Mode)..."
"$PROTON_BIN" run "$GAME_EXE" -screen-fullscreen 0 &
GAME_PID=$!

echo "Game started with PID: $GAME_PID"
echo "---------------------------------------------------"
echo "To play music on this instance, run in another terminal:"
echo "uv run run_music.py --device-path $DEVICE_PATH <midi_file>"
echo "---------------------------------------------------"

wait $GAME_PID
echo "Game exited."
