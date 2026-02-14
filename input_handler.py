import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evdev import UInput

try:
    from evdev import InputDevice as _InputDevice
    from evdev import UInput as _UInput
    from evdev import ecodes as e
except ImportError:
    _UInput = None
    _InputDevice = None
    e = None


class InputHandler:
    """
    Abstracts input handling using evdev.
    """

    def __init__(
        self,
        key_mapping: dict[int, int | list[int]],
        dry_run: bool = False,
        device_path: str | None = None,
        device_name: str = "HertopiaVirtualKeyboard",
    ):
        self.dry_run = dry_run
        self.ui: "UInput | None" = None
        self.key_mapping = key_mapping

        if not self.dry_run and _UInput and e:
            try:
                if device_path and _InputDevice:
                    # Connect to an existing device created by device_manager.py
                    self.ui = _InputDevice(device_path)  # type: ignore
                else:
                    # Create a new UInput device
                    # UInput expects Dict[int, Sequence[int]] | None
                    # Flatten the values list because it might contain lists if multiple keys are mapped to one note
                    vals: list[int] = []
                    for v in self.key_mapping.values():
                        if isinstance(v, list):
                            vals.extend(v)
                        else:
                            vals.append(v)

                    cap = {e.EV_KEY: vals}
                    self.ui = _UInput(cap, name=device_name, version=0x1)
            except PermissionError:
                print("Error: Permission denied. You must run this script with 'sudo'.")
                raise
            except Exception as ex:
                print(f"Error initializing input device: {ex}")
                raise

    def press(self, key_code: int, duration: float = 0.1) -> None:
        """Simulates a key press with a specific duration."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 1)  # Press # type: ignore
            self.ui.write(e.EV_SYN, e.SYN_REPORT, 0)  # type: ignore
            time.sleep(duration)
            self.ui.write(e.EV_KEY, key_code, 0)  # Release # type: ignore
            self.ui.write(e.EV_SYN, e.SYN_REPORT, 0)  # type: ignore
        except Exception as ex:
            if not self.dry_run:
                print(f"Error pressing key: {ex}")

    def key_down(self, key_code: int) -> None:
        """Simulates a key down event."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 1)  # type: ignore
            self.ui.write(e.EV_SYN, e.SYN_REPORT, 0)  # type: ignore
        except Exception as ex:
            if not self.dry_run:
                print(f"Error key down: {ex}")

    def key_up(self, key_code: int) -> None:
        """Simulates a key up event."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 0)  # type: ignore
            self.ui.write(e.EV_SYN, e.SYN_REPORT, 0)  # type: ignore
        except Exception as ex:
            if not self.dry_run:
                print(f"Error key up: {ex}")

    def cleanup(self) -> None:
        """Releases all keys and closes the UInput device."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            # Release all mapped keys to be safe
            for k in self.key_mapping.values():
                if isinstance(k, list):
                    for sub_k in k:
                        self.ui.write(e.EV_KEY, sub_k, 0)
                else:
                    self.ui.write(e.EV_KEY, k, 0)  # type: ignore
            self.ui.write(e.EV_SYN, e.SYN_REPORT, 0)  # type: ignore
            self.ui.close()
        except Exception as ex:
            print(f"Error cleanup: {ex}")
