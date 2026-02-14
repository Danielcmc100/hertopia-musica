#!/usr/bin/env python3
import os
import sys

import evdev
from Xlib import X, display
from Xlib.ext import xtest


def main():
    if len(sys.argv) < 2:
        print("Usage: input_bridge.py <device_path>")
        sys.exit(1)

    device_path = sys.argv[1]

    if not os.path.exists(device_path):
        print(f"Error: Device {device_path} not found.")
        sys.exit(1)

    print(f"Bridge: Opening device {device_path}...", flush=True)
    try:
        dev = evdev.InputDevice(device_path)
    except Exception as e:
        print(f"Error opening device: {e}")
        sys.exit(1)

    # Connect to X Display (from env DISPLAY)
    try:
        d = display.Display()
        print(f"Bridge: Connected to X Display {os.environ.get('DISPLAY')}", flush=True)
    except Exception as e:
        print(f"Error connecting to X display: {e}")
        sys.exit(1)

    print("Bridge: Listening for events...", flush=True)

    # Find the game window (or any mapped window) and focus it
    root = d.screen().root

    def focus_game_window():
        children = root.query_tree().children
        for window in children:
            # Simple heuristic: focus the first mapped window that isn't root
            if window.get_attributes().map_state == X.IsViewable:
                d.set_input_focus(window, X.RevertToParent, X.CurrentTime)
                d.sync()
                # print(f"Bridge: Focused window {window.id}", flush=True)
                return True
        return False

    # Grab device to prevent double input if running on same X server (optional, but good)
    # dev.grab()

    for event in dev.read_loop():
        # Periodically ensure focus (simple hack, better would be event listener)
        # focus_game_window()

        if event.type == evdev.ecodes.EV_KEY:
            # Linux input keycode to X11 keycode mapping is usually +8
            x_keycode = event.code + 8

            # 0 = Release, 1 = Press, 2 = Repeat
            focus_game_window()  # Ensure game is focused before keypress

            if event.value == 1:  # Press
                xtest.fake_input(d, X.KeyPress, x_keycode)
                d.sync()
            elif event.value == 0:  # Release
                xtest.fake_input(d, X.KeyRelease, x_keycode)
                d.sync()
            # We treat Repeat (2) as Press for games that need it, or ignore?
            # Games usually handle repeat themselves or use raw events.
            # safe to forward repeats as KeyPress
            elif event.value == 2:
                xtest.fake_input(d, X.KeyPress, x_keycode)
                d.sync()


if __name__ == "__main__":
    main()
