#!/bin/bash

# Configuration
INSTANCE_ID="${1:-1}" # Default to instance 1 if not provided
DEVICE_NAME="HertopiaBot_${INSTANCE_ID}_$$"
DEVICE_MANAGER_SCRIPT="device_manager.py"
WORK_DIR=$(dirname "$(realpath "$0")")
DEVICE_FILE=".device_${INSTANCE_ID}"

# 0. Pre-launch Cleanup (Only kill my own stale PID if needed? 
# We can't killall anymore if we want multiple instances.
# So we rely on strict PID tracking via trap.)
echo "Starting Instance $INSTANCE_ID..."

# 1. Start Device Manager (Background)
echo "Starting Device Manager..."
LOG_FILE=$(mktemp)
python3 "$WORK_DIR/$DEVICE_MANAGER_SCRIPT" --name "$DEVICE_NAME" > "$LOG_FILE" 2>&1 &
DEVICE_PID=$!

# Wait for device path
echo "Waiting for device creation..."
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
echo "$DEVICE_PATH" > "$DEVICE_FILE"
echo "Device PID: $DEVICE_PID"

# Cleanup on exit
cleanup() {
    echo "Cleaning up Instance $INSTANCE_ID..."
    rm -f "$DEVICE_FILE"
    # Kill Bridge FIRST to avoid "No such device" error
    if [ ! -z "$BRIDGE_PID" ]; then kill $BRIDGE_PID 2>/dev/null; fi
    # Kill Device Manager SECOND
    kill $DEVICE_PID 2>/dev/null
    # Kill Game if still running
    if [ ! -z "$GAME_PID" ]; then kill $GAME_PID 2>/dev/null; fi
    
    # DO NOT use global killall here anymore!
}
trap cleanup EXIT INT TERM

# 2. Start Input Bridge (Background)
# Explicitly target MAIN DISPLAY :0
export DISPLAY=:0
echo "Starting Input Bridge for window 'Heartopia_$INSTANCE_ID'..."
uv run --with python-xlib input_bridge.py "$DEVICE_PATH" --window "Heartopia_$INSTANCE_ID" &
BRIDGE_PID=$!

# 3. Launch Game mimicking Heroic
# Proton Configuration
PROTON_BIN="/home/daniel/.config/heroic/tools/proton/GE-Proton-latest/proton"
WINE_PREFIX="/home/daniel/Games/Heroic/Prefixes/default/Heartopia"
GAME_EXE="/home/daniel/.local/share/Steam/steamapps/common/Heartopia/xdt.exe"
# Start in directory
cd "$(dirname "$GAME_EXE")"

export STEAM_COMPAT_DATA_PATH="$WINE_PREFIX"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="/home/daniel/.local/share/Steam"
export WINEPREFIX="$WINE_PREFIX"

# Trick: Use Wine Virtual Desktop to keep game "focused" internally
# and prevent minimization/focus loss signal from reaching the game logic.
export SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0
export SDL_BACKGROUND_INPUT=1 

# Enable Gamemode if available (Heroic uses it)
if command -v gamemoderun &> /dev/null; then
    LAUNCHER="gamemoderun"
    echo "Using GameMode..."
else
    LAUNCHER=""
fi

echo "Launching Heartopia in Wine Virtual Desktop (Heartopia_$INSTANCE_ID)..."
# Use eval or conditional to handle empty LAUNCHER correctly
if [ -n "$LAUNCHER" ]; then
    "$LAUNCHER" "$PROTON_BIN" run explorer /desktop=Heartopia_$INSTANCE_ID,800x600 "$GAME_EXE" -runInBackground &
else
    "$PROTON_BIN" run explorer /desktop=Heartopia_$INSTANCE_ID,800x600 "$GAME_EXE" -runInBackground &
fi
GAME_PID=$!

echo "Game started with PID: $GAME_PID"
echo "---------------------------------------------------"
echo "To play music on this instance, run in another terminal:"
echo "uv run run_music.py --device-path $DEVICE_PATH <midi_file>"
echo "---------------------------------------------------"

# Wait for game to close
# Wait for game to close
# When using explorer /desktop, the initial PID might exit early.
# We need to wait for the actual game binary.

echo "Waiting for window 'Heartopia_$INSTANCE_ID' (or suffixed) to appear..."
# Wait up to 60 seconds for the window to start
match_found=false
WINDOW_NAME=""

check_window() {
    if xwininfo -name "Heartopia_$INSTANCE_ID" > /dev/null 2>&1; then
        WINDOW_NAME="Heartopia_$INSTANCE_ID"
        return 0
    elif xwininfo -name "Heartopia_$INSTANCE_ID - Wine Desktop" > /dev/null 2>&1; then
        WINDOW_NAME="Heartopia_$INSTANCE_ID - Wine Desktop"
        return 0
    fi
    return 1
}

for i in {1..60}; do
    if check_window; then
        match_found=true
        break
    fi
    sleep 1
done

if [ "$match_found" = false ]; then
    echo "Error: Timed out waiting for window 'Heartopia_$INSTANCE_ID'."
    exit 1
fi

echo "Window found: '$WINDOW_NAME'. Configuring monitoring..."

echo "Starting Input Bridge for window '$WINDOW_NAME'..."
# Log bridge output for debugging (in WORK_DIR)
BRIDGE_LOG="$WORK_DIR/bridge_${INSTANCE_ID}.log"
# Run uv from the project directory to ensure access to script and environment
uv run --directory "$WORK_DIR" --with python-xlib input_bridge.py "$DEVICE_PATH" --window "$WINDOW_NAME" > "$BRIDGE_LOG" 2>&1 &
BRIDGE_PID=$!

echo "Monitoring window '$WINDOW_NAME'..."
while xwininfo -name "$WINDOW_NAME" > /dev/null 2>&1; do
    sleep 2
done

echo "Game process exited."
# GAME_EXIT_CODE=$? # We can't easily get the exit code of the game itself this way
