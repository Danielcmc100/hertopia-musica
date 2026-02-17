#!/usr/bin/env python3
import select
import sys

import evdev

print("=== Find Mouse Device ===")
print("Scanning for input devices...")

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
mouse_devices = []

for device in devices:
    # Check if device has mouse capabilities (BTN_LEFT)
    # capabilities() returns a dict, checked against evdev.ecodes.EV_KEY
    caps = device.capabilities()
    if evdev.ecodes.EV_KEY in caps:
        keys = caps[evdev.ecodes.EV_KEY]
        if evdev.ecodes.BTN_LEFT in keys:
            mouse_devices.append(device)
            print(f"Found candidate: {device.path} - {device.name}")

if not mouse_devices:
    print(
        "No mouse devices found! Ensure you have permissions (try sudo or add to input group)."
    )
    sys.exit(1)

print("\nPlease move your mouse or click a button to identify the correct device.")
print("Press Ctrl+C to stop.")

# Monitor devices
fds = {dev.fd: dev for dev in mouse_devices}
try:
    while True:
        r, w, x = select.select(fds, [], [])
        for fd in r:
            dev = fds[fd]
            for event in dev.read():
                if (
                    event.type == evdev.ecodes.EV_KEY
                    or event.type == evdev.ecodes.EV_REL
                ):
                    print(f"\nActivity detected on: {dev.path} ({dev.name})")
                    print(f"Event: {evdev.categorize(event)}")
                    print(f"--> THIS IS LIKELY YOUR MOUSE: {dev.path}")

                    # Optional: Save to config?
                    # For now just print.
                    sys.exit(0)
except KeyboardInterrupt:
    pass
