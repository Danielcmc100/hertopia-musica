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
from PIL import Image

print("=== Grid Calibration (Auto-Resolution) ===")

# 1. Detect Screen Resolution via Screenshot
# This ensures our coordinates match what automation sees.
print("Detecting screen resolution...")

# Sudo/User logic for screenshot
SUDO_USER = os.environ.get("SUDO_USER")
SUDO_UID = os.environ.get("SUDO_UID")
outfile = "/tmp/calib_res_check.png"

try:
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
    width = img.width
    height = img.height
    print(f"Detected Resolution: {width}x{height}")

except Exception as ex:
    print(f"Error detecting resolution: {ex}")
    print("Please enter manually:")
    try:
        width = int(input("Total Screen Width: "))
        height = int(input("Total Screen Height: "))
    except ValueError:
        sys.exit(1)

# Init Virtual Absolute Mouse
cap = {
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
    e.EV_ABS: [
        (e.ABS_X, AbsInfo(value=0, min=0, max=width, fuzz=0, flat=0, resolution=0)),
        (e.ABS_Y, AbsInfo(value=0, min=0, max=height, fuzz=0, flat=0, resolution=0)),
    ],
}

ui = UInput(cap, name="Hertopia-Tablet-Mouse", version=0x1)
time.sleep(1)

current_x = width // 2
current_y = height // 2


def move_to(x, y):
    global current_x, current_y
    # Clamp
    x = max(0, min(width, x))
    y = max(0, min(height, y))

    ui.write(e.EV_ABS, e.ABS_X, int(x))
    ui.write(e.EV_ABS, e.ABS_Y, int(y))
    ui.syn()
    current_x = x
    current_y = y


move_to(current_x, current_y)


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def interactive_move(target_name):
    global current_x, current_y
    print(f"\n--- Move to {target_name} ---")
    print("Use w/a/s/d for slow, W/A/S/D for fast.")
    print("Press SPACE to mark position.")

    while True:
        k = getch()
        dx = 0
        dy = 0

        if k == "w":
            dy = -1
        elif k == "s":
            dy = 1
        elif k == "a":
            dx = -1
        elif k == "d":
            dx = 1
        elif k == "W":
            dy = -20
        elif k == "S":
            dy = 20
        elif k == "A":
            dx = -20
        elif k == "D":
            dx = 20
        elif k == " ":
            print(f"\nMarked {target_name}: {current_x},{current_y}")
            return current_x, current_y
        elif k == "\x03":
            sys.exit(1)

        move_to(current_x + dx, current_y + dy)
        print(f"\rPos: {current_x},{current_y}   ", end="")


print("\nMove cursor to TOP-LEFT of the Grid.")
x1, y1 = interactive_move("TOP-LEFT")

print("\nMove cursor to BOTTOM-RIGHT of the Grid.")
x2, y2 = interactive_move("BOTTOM-RIGHT")

# --- Validation ---
grid_w = abs(x2 - x1)
grid_h = abs(y2 - y1)
ppp_x = grid_w / 150.0
ppp_y = grid_h / 150.0

print("\n--- Calibration Check ---")
print(f"Selected Area: {grid_w}x{grid_h}")
print(f"Pixels per Dot (X): {ppp_x:.4f}")
print(f"Pixels per Dot (Y): {ppp_y:.4f}")

is_bad = False
if abs(ppp_x - round(ppp_x)) > 0.1 or abs(ppp_y - round(ppp_y)) > 0.1:
    print("\n[WARNING] The grid alignment seems OFF!")
    print("The number of pixels per dot is not a whole number.")
    print("This will cause gaps or misaligned drawing.")
    is_bad = True
else:
    print("\n[OK] Alignment looks good!")

if is_bad:
    print("Tip: Use W/A/S/D to move faster and w/a/s/d for precision.")
    ans = input("Do you want to Save anyway? (y/N): ").lower()
    if ans != "y":
        print("Calibration aborted.")
        sys.exit(1)
# ------------------

config = {
    "resolution": {"width": width, "height": height},
    "grid": {
        "top_left": {"x": x1, "y": y1},
        "bottom_right": {"x": x2, "y": y2},
        "width": 150,
        "height": 150,
    },
}

with open("grid.json", "w") as f:
    json.dump(config, f, indent=2)

print("\nSaved grid.json (Auto-Res)!")
