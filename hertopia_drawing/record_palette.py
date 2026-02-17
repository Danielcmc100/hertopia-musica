#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import termios
import time
import tty

from evdev import AbsInfo, UInput
from evdev import ecodes as e

# Configuration
IS_GNOME = True
DOUBLE_CLICK_NEEDED = True

# Load Resolution
try:
    with open("grid.json", "r") as f:
        grid_config = json.load(f)
        RES = grid_config.get("resolution", {})
        WIDTH = RES.get("width")
        HEIGHT = RES.get("height")
        if not WIDTH or not HEIGHT:
            raise ValueError
except Exception:
    print(
        "Error: grid.json missing or missing resolution. Run calibrate_grid.py first!"
    )
    sys.exit(1)

print("=== Palette Recorder (Fix: Sudo Screenshot) ===")

# Detect running as sudo
SUDO_USER = os.environ.get("SUDO_USER")
SUDO_UID = os.environ.get("SUDO_UID")

if SUDO_USER:
    print(f"Running as Root (Sudo). Will execute screenshot as user: {SUDO_USER}")
else:
    print(
        "Running as current user (might fail to create uinput device if not in group)."
    )

# Init Abs Mouse
cap = {
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
    e.EV_ABS: [
        (e.ABS_X, AbsInfo(value=0, min=0, max=WIDTH, fuzz=0, flat=0, resolution=0)),
        (e.ABS_Y, AbsInfo(value=0, min=0, max=HEIGHT, fuzz=0, flat=0, resolution=0)),
    ],
}

try:
    ui = UInput(cap, name="Hertopia-Tablet-Mouse", version=0x1)
except PermissionError:
    print("\nERROR: Permission denied creating uinput device.")
    print("Run this script with 'sudo'.")
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


move_to(current_x, current_y)


def click():
    ui.write(e.EV_KEY, e.BTN_LEFT, 1)
    ui.syn()
    time.sleep(0.05)
    ui.write(e.EV_KEY, e.BTN_LEFT, 0)
    ui.syn()
    time.sleep(0.05)
    ui.write(e.EV_KEY, e.BTN_LEFT, 1)
    ui.syn()
    time.sleep(0.05)
    ui.write(e.EV_KEY, e.BTN_LEFT, 0)
    ui.syn()
    time.sleep(0.05)


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def get_color():
    try:
        # Construct screenshot command
        # We need to run AS THE USER to access the display/dbus

        outfile = "/tmp/pixel_hertopia.png"

        if SUDO_USER:
            # We assume standard DBus path: /run/user/<uid>/bus
            # And standard Display: :0 (usually) or Wayland-0
            # We try to infer or pass existing vars if preserved, but usually they aren't.
            # Let's try explicit hardcoded guess which is robust on Ubuntu.

            dbus_addr = f"unix:path=/run/user/{SUDO_UID}/bus"

            # Use 'runuser' or 'sudo -u'
            # We need to set DBUS_SESSION_BUS_ADDRESS
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

        # Capture
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        from PIL import Image

        img = Image.open(outfile)

        # Verify resolution match?
        if img.width != WIDTH or img.height != HEIGHT:
            # Only warn once
            if not hasattr(get_color, "warned"):
                print(
                    f"\n[WARNING] Screenshot size ({img.width}x{img.height}) != Grid Resolution ({WIDTH}x{HEIGHT}). Coordinates might be off!"
                )
                get_color.warned = True

        safe_x = min(current_x, img.width - 1)
        safe_y = min(current_y, img.height - 1)

        rgb = img.getpixel((safe_x, safe_y))

        # Check for black
        if rgb == (0, 0, 0):
            # Might be valid, but suspicious
            pass

        return list(rgb)

    except Exception:
        # print(f"\rDebug Capture Error: {e}")
        return [0, 0, 0]


def interactive_move(prompt):
    global current_x, current_y
    print(f"\n>> {prompt}")
    print("   (WASD, SPACE, 'c')")

    while True:
        k = getch()
        dx = 0
        dy = 0
        if k == "w":
            dy = -5
        elif k == "s":
            dy = 5
        elif k == "a":
            dx = -5
        elif k == "d":
            dx = 5
        elif k == "W":
            dy = -50
        elif k == "S":
            dy = 50
        elif k == "A":
            dx = -50
        elif k == "D":
            dx = 50
        elif k == " ":
            print(f"   Recorded: {current_x},{current_y}")
            return (current_x, current_y)
        elif k == "c":
            print("   (Click)", end="\r")
            click()
        elif k == "q":
            sys.exit(0)

        if dx or dy:
            move_to(current_x + dx, current_y + dy)
            print(f"\r   Pos: {current_x},{current_y}  ", end="")


# --- 1. Globals ---
print("\n--- Phase 1: Global Setup ---")
print("Move to 'PALETTE ICON'.")
palette_icon = interactive_move("Palette Icon")

print("Open sub-menu.")
print("Move to 'BACK ARROW'.")
back_btn = interactive_move("Back Button")

# --- 2. Sub-Color Grid ---
print("\n--- Phase 2: Record Sub-Colors ---")
sub_color_positions = []
for i in range(9):
    pos = interactive_move(f"Sub-Color #{i + 1}")
    sub_color_positions.append(pos)

print("Closing sub-menu...")
move_to(back_btn[0], back_btn[1])
click()

# --- 3. Main Colors ---
print("\n--- Phase 3: Main Colors ---")
palette_data = []
palette_count = 0

while True:
    print("\n----------------")
    main_loc = interactive_move("Move to MAIN COLOR. SPACE to record.")

    print("   Capturing... ", end="", flush=True)
    main_rgb = get_color()
    print(f"{main_rgb}")

    print("Sub-Group? (y/n)")
    while True:
        k = getch()
        if k == "y":
            has_sub = True
            break
        elif k == "n":
            has_sub = False
            break

    palette_data.append(
        {"rgb": main_rgb, "type": "main", "loc": main_loc, "sub_index": -1}
    )

    if has_sub:
        # Click Main Color to ensure it is focused
        click()
        time.sleep(0.5)

        # Click Palette Icon to open sub-menu
        move_to(palette_icon[0], palette_icon[1])
        click()
        time.sleep(1.2)

        if palette_count == 0:
            print(
                "   [Manual Mode] First palette: Please set positions manually (5 colors)."
            )
            for i in range(5):
                # Manual interaction for the first unique palette
                s_loc = interactive_move(f"First Palette - Sub #{i + 1}")
                move_to(s_loc[0], s_loc[1])  # Ensure we are there
                time.sleep(0.3)
                s_rgb = get_color()
                print(f"     Sub #{i + 1}: {s_rgb}")
                palette_data.append(
                    {"rgb": s_rgb, "type": "sub", "loc": main_loc, "sub_index": i}
                )
        else:
            print("   [Auto Mode] Scanning standard grid...")
            # Standard auto-scan for subsequent palettes
            for idx, pos in enumerate(sub_color_positions):
                move_to(pos[0], pos[1])
                time.sleep(0.3)
                s_rgb = get_color()
                print(f"     Sub #{idx + 1}: {s_rgb}")
                palette_data.append(
                    {"rgb": s_rgb, "type": "sub", "loc": main_loc, "sub_index": idx}
                )

        # Go Back
        move_to(back_btn[0], back_btn[1])
        click()
        time.sleep(0.8)

    print("More Main? (y/n)")
    while True:
        k = getch()
        if k == "y":
            break
        elif k == "n":
            break
    palette_count += 1
    if k == "n":
        break

# Save
output = {
    "buttons": {"palette_icon": palette_icon, "back": back_btn},
    "sub_positions": sub_color_positions,
    "colors": palette_data,
}
with open("palette.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nSaved palette.json!")
