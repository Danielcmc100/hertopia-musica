import time
from typing import TYPE_CHECKING, Sequence, cast

if TYPE_CHECKING:
    from evdev import UInput

try:
    from evdev import UInput as _UInput
    from evdev import ecodes as e
except ImportError:
    _UInput = None
    e = None


class InputHandler:
    """
    Abstracts input handling using evdev.
    """

    def __init__(self, key_mapping: dict[int, int], dry_run: bool = False):
        self.dry_run = dry_run
        self.ui: "UInput | None" = None
        self.key_mapping = key_mapping

        if not self.dry_run and _UInput and e:
            try:
                # UInput expects Dict[int, Sequence[int]] | None
                vals = cast(Sequence[int], list(self.key_mapping.values()))
                cap = {e.EV_KEY: vals}
                self.ui = _UInput(cap, name="HertopiaVirtualKeyboard", version=0x1)
            except PermissionError:
                print("Error: Permission denied. You must run this script with 'sudo'.")
                raise

    def press(self, key_code: int, duration: float = 0.1) -> None:
        """Simulates a key press with a specific duration."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 1)  # Press
            self.ui.syn()
            time.sleep(duration)
            self.ui.write(e.EV_KEY, key_code, 0)  # Release
            self.ui.syn()
        except Exception:
            pass

    def key_down(self, key_code: int) -> None:
        """Simulates a key down event."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 1)
            self.ui.syn()
        except Exception:
            pass

    def key_up(self, key_code: int) -> None:
        """Simulates a key up event."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            self.ui.write(e.EV_KEY, key_code, 0)
            self.ui.syn()
        except Exception:
            pass

    def cleanup(self) -> None:
        """Releases all keys and closes the UInput device."""
        if self.dry_run or not self.ui or not e:
            return

        try:
            # Release all mapped keys to be safe
            for k in self.key_mapping.values():
                self.ui.write(e.EV_KEY, k, 0)
            self.ui.syn()
            self.ui.close()
        except Exception:
            pass
