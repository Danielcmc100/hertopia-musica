import argparse
import os
import signal
import sys
import time
from typing import NoReturn

try:
    import evdev
    from evdev import UInput
    from evdev import ecodes as e
except ImportError:
    print("Error: 'evdev' library not found. Install it with 'pip install evdev'")
    sys.exit(1)


def signal_handler(sig, frame):
    print("\nExiting...", flush=True)
    sys.exit(0)


def find_device_path(name: str) -> str | None:
    """Find the device path for a uinput device by its name."""
    for event in os.listdir("/dev/input/"):
        if not event.startswith("event"):
            continue
        path = os.path.join("/dev/input/", event)
        try:
            device = evdev.InputDevice(path)
            if device.name == name:
                return path
        except Exception:
            # print(f"Debug: Failed to check {path}: {e}", flush=True)
            continue
    return None


def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="Create a persistent uinput device.")
    parser.add_argument(
        "--name",
        type=str,
        default="HertopiaVirtualKeyboard",
        help="Name of the virtual input device",
    )
    args = parser.parse_args()

    keys = [
        e.KEY_A,
        e.KEY_B,
        e.KEY_C,
        e.KEY_D,
        e.KEY_E,
        e.KEY_F,
        e.KEY_G,
        e.KEY_H,
        e.KEY_I,
        e.KEY_J,
        e.KEY_K,
        e.KEY_L,
        e.KEY_M,
        e.KEY_N,
        e.KEY_O,
        e.KEY_P,
        e.KEY_Q,
        e.KEY_R,
        e.KEY_S,
        e.KEY_T,
        e.KEY_U,
        e.KEY_V,
        e.KEY_W,
        e.KEY_X,
        e.KEY_Y,
        e.KEY_Z,
        e.KEY_1,
        e.KEY_2,
        e.KEY_3,
        e.KEY_4,
        e.KEY_5,
        e.KEY_6,
        e.KEY_7,
        e.KEY_8,
        e.KEY_9,
        e.KEY_0,
        e.KEY_MINUS,
        e.KEY_EQUAL,
        e.KEY_BACKSPACE,
        e.KEY_TAB,
        e.KEY_LEFTBRACE,
        e.KEY_RIGHTBRACE,
        e.KEY_ENTER,
        e.KEY_LEFTCTRL,
        e.KEY_SEMICOLON,
        e.KEY_APOSTROPHE,
        e.KEY_GRAVE,
        e.KEY_LEFTSHIFT,
        e.KEY_BACKSLASH,
        e.KEY_COMMA,
        e.KEY_DOT,
        e.KEY_SLASH,
        e.KEY_RIGHTSHIFT,
        e.KEY_KPASTERISK,
        e.KEY_LEFTALT,
        e.KEY_SPACE,
        e.KEY_CAPSLOCK,
        e.KEY_F1,
        e.KEY_F2,
        e.KEY_F3,
        e.KEY_F4,
        e.KEY_F5,
        e.KEY_F6,
        e.KEY_F7,
        e.KEY_F8,
        e.KEY_F9,
        e.KEY_F10,
        e.KEY_NUMLOCK,
        e.KEY_SCROLLLOCK,
        e.KEY_KP7,
        e.KEY_KP8,
        e.KEY_KP9,
        e.KEY_KPMINUS,
        e.KEY_KP4,
        e.KEY_KP5,
        e.KEY_KP6,
        e.KEY_KPPLUS,
        e.KEY_KP1,
        e.KEY_KP2,
        e.KEY_KP3,
        e.KEY_KP0,
        e.KEY_KPDOT,
        e.KEY_F11,
        e.KEY_F12,
        e.KEY_RO,
        e.KEY_KATAKANA,
        e.KEY_HIRAGANA,
        e.KEY_HENKAN,
        e.KEY_KATAKANAHIRAGANA,
        e.KEY_MUHENKAN,
        e.KEY_KPJPCOMMA,
        e.KEY_KPENTER,
        e.KEY_RIGHTCTRL,
        e.KEY_KPSLASH,
        e.KEY_SYSRQ,
        e.KEY_RIGHTALT,
        e.KEY_LINEFEED,
        e.KEY_HOME,
        e.KEY_UP,
        e.KEY_PAGEUP,
        e.KEY_LEFT,
        e.KEY_RIGHT,
        e.KEY_END,
        e.KEY_DOWN,
        e.KEY_PAGEDOWN,
        e.KEY_INSERT,
        e.KEY_DELETE,
    ]

    cap = {e.EV_KEY: keys}

    try:
        # Create the uinput device
        ui = UInput(cap, name=args.name, version=0x1)

        # Wait and find path manually if ui.device is None
        dev_path = None
        for i in range(50):
            if hasattr(ui, "device") and ui.device:
                dev_path = ui.device.path
                break
            # Fallback manual scan
            dev_path = find_device_path(args.name)
            if dev_path:
                break
            time.sleep(0.1)

        if not dev_path:
            raise Exception("Timeout: Could not find the created device path.")

        print(f"DEVICE_PATH={dev_path}", flush=True)
        print(f"Device '{args.name}' created successfully at {dev_path}", flush=True)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while True:
            time.sleep(1)

    except PermissionError:
        print("Error: Permission denied accessing /dev/uinput.", flush=True)
        sys.exit(1)
    except Exception as err:
        print(f"Error: {err}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
