#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

from evdev import AbsInfo, UInput
from evdev import ecodes as e
from PIL import Image

# Configuration
SUDO_USER = os.environ.get("SUDO_USER")
SUDO_UID = os.environ.get("SUDO_UID")

print("=== Palette Color Extractor ===")
print("Re-scanning colors based on recorded positions in palette.json...")

# Load Configs
try:
    with open("grid.json", "r") as f:
        grid_config = json.load(f)
        RES = grid_config.get("resolution", {})
        WIDTH = RES.get("width")
        HEIGHT = RES.get("height")

    with open("palette.json", "r") as f:
        palette_data = json.load(f)
        buttons = palette_data["buttons"]
        sub_positions = palette_data.get("sub_positions", [])  # Should be list of [x,y]
        colors = palette_data["colors"]

except Exception as ex:
    print(f"Error loading configs: {ex}")
    sys.exit(1)

# Init UInput
cap = {
    e.EV_KEY: [e.BTN_LEFT],
    e.EV_ABS: [
        (e.ABS_X, AbsInfo(value=0, min=0, max=WIDTH, fuzz=0, flat=0, resolution=0)),
        (e.ABS_Y, AbsInfo(value=0, min=0, max=HEIGHT, fuzz=0, flat=0, resolution=0)),
    ],
}

try:
    ui = UInput(cap, name="Hertopia-Tablet-Mouse", version=0x1)
except PermissionError:
    print("Run with sudo!")
    sys.exit(1)

time.sleep(1)
current_x = WIDTH // 2
current_y = HEIGHT // 2


def move_to(x, y):
    global current_x, current_y
    x = int(max(0, min(WIDTH, x)))
    y = int(max(0, min(HEIGHT, y)))
    ui.write(e.EV_ABS, e.ABS_X, x)
    ui.write(e.EV_ABS, e.ABS_Y, y)
    ui.syn()
    current_x = x
    current_y = y
    time.sleep(0.005)  # Fast move


def click():
    ui.write(e.EV_KEY, e.BTN_LEFT, 1)
    ui.syn()
    time.sleep(0.05)
    ui.write(e.EV_KEY, e.BTN_LEFT, 0)
    ui.syn()
    time.sleep(0.05)
    # Double click just in case? user liked it.
    ui.write(e.EV_KEY, e.BTN_LEFT, 1)
    ui.syn()
    time.sleep(0.05)
    ui.write(e.EV_KEY, e.BTN_LEFT, 0)
    ui.syn()
    time.sleep(0.05)


def get_color():
    try:
        outfile = "/tmp/extract_pixel.png"
        if SUDO_USER:
            dbus_addr = f"unix:path=/run/user/{SUDO_UID}/bus"
            cmd = [
                "sudo",
                "-u",
                SUDO_USER,
                "env",
                f"DBUS_SESSION_BUS_ADDRESS={dbus_addr}",
                "gnome-screenshot",
                "-f",
                outfile,
            ]
        else:
            cmd = ["gnome-screenshot", "-f", outfile]

        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        img = Image.open(outfile)
        safe_x = min(current_x, img.width - 1)
        safe_y = min(current_y, img.height - 1)
        return list(img.getpixel((safe_x, safe_y)))
    except Exception as e:
        print(f"Cap Err: {e}")
        return [0, 0, 0]


# --- Execution ---
# We iterate through colors.
# We need to track state: Are we in a sub-menu? Which main color is active?

current_state = "ROOT"  # ROOT or SUBMENU

print(f"Processing {len(colors)} colors. Please Switch to Game Window!")
time.sleep(3)

# Reset mouse
move_to(0, 0)
time.sleep(0.1)

# To optimize: We rely on the order of `colors` list matching the UI flow.
# Main -> Sub -> Sub... -> Main -> Sub...

for i, color in enumerate(colors):
    ctype = color["type"]
    main_loc = color["loc"]

    # 1. Navigate to location
    if ctype == "main":
        if current_state == "SUBMENU":
            # Exit previous sub-menu
            print("  < Exiting Sub-Menu")
            bx, by = buttons["back"]
            move_to(bx, by)
            click()
            time.sleep(0.8)
            current_state = "ROOT"

        move_to(main_loc[0], main_loc[1])
        # We perform a click to select it (and thus reveal its color clearly?)
        # Or just hover? Usually hover shows highlight.
        # But to open sub-menu later we need it selected.
        # Let's click it.
        click()
        time.sleep(0.2)

        rgb = get_color()
        color["rgb"] = rgb
        print(f"[{i + 1}/{len(colors)}] MAIN: {rgb}")

    elif ctype == "sub":
        if current_state == "ROOT":
            # Enter Sub-Menu
            print("  > Entering Sub-Menu")
            # Ensure main is selected (it should be from previous iteration)
            move_to(main_loc[0], main_loc[1])
            click()
            time.sleep(0.1)

            px, py = buttons["palette_icon"]
            move_to(px, py)
            click()
            time.sleep(1.2)  # Wait for anim
            current_state = "SUBMENU"

        # Move to Sub Pos
        s_idx = color["sub_index"]
        # Use recorded sub_positions if available (preferred)
        if sub_positions and s_idx < len(sub_positions):
            sx, sy = sub_positions[s_idx]
        else:
            # Fallback if manual edit didn't include sub_positions list?
            # But the view_file showed it has them.
            print("Error: Missing sub_positions index")
            continue

        move_to(sx, sy)
        time.sleep(0.1)  # Hover wait
        rgb = get_color()
        color["rgb"] = rgb
        print(f"[{i + 1}/{len(colors)}] SUB #{s_idx}: {rgb}")

# Final Cleanup
if current_state == "SUBMENU":
    bx, by = buttons["back"]
    move_to(bx, by)
    click()

# Save Update
palette_data["colors"] = colors
with open("palette.json", "w") as f:
    json.dump(palette_data, f, indent=2)

print("\nDONE! Extracted colors saved to palette.json.")
