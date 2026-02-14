from evdev import UInput
from evdev import ecodes as e

try:
    cap = {e.EV_KEY: [e.KEY_A]}
    ui = UInput(cap, name="TestDevice")
    print(f"ui: {ui}")
    print(f"dir(ui): {dir(ui)}")
    if hasattr(ui, "device"):
        print(f"ui.device: {ui.device}")
        if ui.device:
            print(f"dir(ui.device): {dir(ui.device)}")
            print(f"ui.device.path: {ui.device.path}")
    if hasattr(ui, "path"):
        print(f"ui.path: {ui.path}")
except Exception as err:
    print(f"Error: {err}")
    import traceback

    traceback.print_exc()
