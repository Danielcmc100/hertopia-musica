#!/bin/bash

# Configuration
DEVICE_NAME="HertopiaBot_$$" # Unique name based on PID
DEVICE_MANAGER_SCRIPT="device_manager.py"
WORK_DIR=$(dirname "$(realpath "$0")")

echo "Starting Device Manager..."
# Start device manager in background and redirect output to a temporary file to capture the device path
LOG_FILE=$(mktemp)
python3 "$WORK_DIR/$DEVICE_MANAGER_SCRIPT" --name "$DEVICE_NAME" > "$LOG_FILE" 2>&1 &
DEVICE_PID=$!

# Wait for the device to be created and path to be printed
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

cat "$LOG_FILE"
rm "$LOG_FILE"

if [ -z "$DEVICE_PATH" ]; then
    echo "Error: Failed to create virtual device."
    kill $DEVICE_PID
    exit 1
fi

echo "Device created at: $DEVICE_PATH"
echo "Device PID: $DEVICE_PID"

# Cleanup function to kill device manager when this script exits
cleanup() {
    echo "Cleaning up..."
    kill $DEVICE_PID
}
trap cleanup EXIT

# --- ACTUAL HEARTORIA LAUNCH COMMAND ---
# Using Proton GE and the prefix found in Heroic configs
PROTON_BIN="/home/daniel/.config/heroic/tools/proton/GE-Proton-latest/proton"
WINE_PREFIX="/home/daniel/Games/Heroic/Prefixes/default/Heartopia"
GAME_EXE="/home/daniel/.local/share/Steam/steamapps/common/Heartopia/xdt.exe"
STEAM_COMPAT_DATA_PATH="$WINE_PREFIX"
STEAM_COMPAT_CLIENT_INSTALL_PATH="/home/daniel/.local/share/Steam"

echo "----------------------------------------------------------------"
echo "SETTING UP CHEAP ISOLATION WITH XEPHYR"
echo "----------------------------------------------------------------"

# Find a free display number
XEPHYR_DISPLAY=":100"
for i in {100..200}; do
    if ! [ -e "/tmp/.X11-unix/X$i" ]; then
        XEPHYR_DISPLAY=":$i"
        break
    fi
done

echo "Starting Xephyr on display $XEPHYR_DISPLAY..."
# Start Xephyr with default input (host keyboard/mouse) so you can still use them if focused.
# But we rely on input_bridge.py for background music input.
# Added -glamor to fix 'amdgpu' crash (enable GPU accel).
Xephyr $XEPHYR_DISPLAY -ac -br -noreset -screen 640x480 &
XEPHYR_PID=$!

echo "Xephyr started (PID: $XEPHYR_PID). Launching input bridge..."

# Launch the input bridge to forward events from our virtual device to Xephyr
# We use 'uv run --with python-xlib' to ensure dependencies are met without polluting global env.
# The bridge needs to know the DISPLAY of Xephyr.
DISPLAY=$XEPHYR_DISPLAY PROTON_LOG=1 uv run --with python-xlib input_bridge.py "$DEVICE_PATH" &
BRIDGE_PID=$!

echo "Input Bridge started (PID: $BRIDGE_PID). Launching Window Manager (Openbox) and game inside..."

# Launch Openbox inside Xephyr to manage window focus. Essential for background input!
DISPLAY=$XEPHYR_DISPLAY openbox &
WM_PID=$!

# Export DISPLAY so the game opens inside Xephyr
export DISPLAY=$XEPHYR_DISPLAY

# Run the game (Directly, Firejail is optional now but we keep it for clean env if desired, 
# but for now let's go direct to minimize complexity)
# We need to set env vars for Proton manually since we are outside Heroic
export STEAM_COMPAT_DATA_PATH="$WINE_PREFIX"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_COMPAT_CLIENT_INSTALL_PATH"
export WINEPREFIX="$WINE_PREFIX"

# FORCE OPENGL (WINED3D) because Xephyr doesn't do Vulkan well
export PROTON_USE_WINED3D=1

"$PROTON_BIN" run "$GAME_EXE" &
GAME_PID=$!

echo "Game started with PID: $GAME_PID on display $XEPHYR_DISPLAY"
echo "To play music on this instance, run:"
echo "python3 run_music.py --device-path $DEVICE_PATH <midi_file>"

# Wait for game to exit
wait $GAME_PID
echo "Game exited. Closing Xephyr and Bridge..."
kill $XEPHYR_PID
kill $BRIDGE_PID
kill $WM_PID


