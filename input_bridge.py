#!/usr/bin/env python3
import argparse
import os
import sys
import time

import evdev
from Xlib import X, display, error
from Xlib.protocol import event as xevent


def main():
    parser = argparse.ArgumentParser(description="Bridge uinput events to X11 window.")
    parser.add_argument("device_path", help="Path to input device")
    parser.add_argument(
        "--window", default="Heartopia", help="Target window name (WM_NAME)"
    )
    args = parser.parse_args()

    device_path = args.device_path
    target_window_name = args.window

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

    # Find the game window on the main display
    root = d.screen().root
    game_window = None

    def find_game_window(root_window=None):
        if root_window is None:
            root_window = root

        # Breadth-first search for better performance maybe? Or DFS is fine.
        # We need to find the window named "Heartopia" which is NOT "Wine Desktop"

        children = []
        try:
            # Basic tree traversal
            tree = root_window.query_tree()
            children = tree.children
        except Exception:
            return None

        # Check children
        for child in children:
            try:
                wm_name = child.get_wm_name()
                # Match strict name or Wine virtual desktop format
                if wm_name and (
                    wm_name == target_window_name
                    or wm_name == f"{target_window_name} - Wine Desktop"
                    or f"{target_window_name} -" in wm_name
                ):
                    return child

                # If we find a window that might be it, but we want to be sure, we could check class.
                # But exact name "Heartopia" is distinct from "Heartopia - Wine Desktop"
            except Exception:
                pass

        # Recurse
        for child in children:
            found = find_game_window(child)
            if found:
                return found

        return None

    # Wait for game window
    print(f"Bridge: Waiting for '{target_window_name}' window...", flush=True)
    for i in range(30):
        game_window = find_game_window()
        if game_window:
            print(f"Bridge: Found Game Window! ID={hex(game_window.id)}", flush=True)
            break
        time.sleep(1)

    if not game_window:
        print("Bridge: Could not find game window. Exiting.", flush=True)
        sys.exit(1)

    for event in dev.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            # Linux input keycode to X11 keycode mapping is usually +8
            x_keycode = event.code + 8

            # Send FocusIn event occasionally to trick game into thinking it has focus
            # Doing this too often might flicker, but let's try just once or periodically?

            try:
                focus_evt = xevent.FocusIn(
                    display=d,
                    window=game_window,
                    detail=X.NotifyDetailNone,
                    mode=X.NotifyNormal,
                )

                # 0 = Release, 1 = Press
                if event.value == 1:  # Press
                    # Send FocusIn before Press
                    game_window.send_event(
                        focus_evt, propagate=False, event_mask=X.FocusChangeMask
                    )
                    d.flush()

                    event_obj = xevent.KeyPress(
                        time=int(time.time()),
                        root=root.id,
                        window=game_window.id,
                        same_screen=1,
                        child=X.NONE,
                        root_x=0,
                        root_y=0,
                        event_x=0,
                        event_y=0,
                        state=0,
                        detail=x_keycode,
                    )
                    game_window.send_event(
                        event_obj, propagate=False, event_mask=X.KeyPressMask
                    )
                    d.flush()

                elif event.value == 0:  # Release
                    event_obj = xevent.KeyRelease(
                        time=int(time.time()),
                        root=root.id,
                        window=game_window.id,
                        same_screen=1,
                        child=X.NONE,
                        root_x=0,
                        root_y=0,
                        event_x=0,
                        event_y=0,
                        state=0,
                        detail=x_keycode,
                    )
                    game_window.send_event(
                        event_obj, propagate=False, event_mask=X.KeyReleaseMask
                    )
                    d.flush()
            except error.XError:
                # print(f"Bridge: X Protocol Error ({e}). Window might be gone. Resetting...")
                # We can be silent or verbose. Let's be silent to avoid spamming user console
                game_window = None
                continue


if __name__ == "__main__":
    main()
