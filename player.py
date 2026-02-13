import threading
import time

import mido
from mido import Message

from input_handler import InputHandler
from mappings import DRUM_MAPPING, GUITAR_MAPPING, KEYBOARD_MAPPING, get_key_name


class MidiPlayer:
    def __init__(
        self,
        midi_file: str,
        speed: float = 1.0,
        transpose: int = 0,
        dry_run: bool = False,
        layout: str = "keyboard",
    ):
        self.midi_file = midi_file
        self.speed = speed
        self.transpose = transpose
        self.dry_run = dry_run
        self.layout = layout

        self.current_mapping: dict[int, int]
        if layout == "guitar":
            self.current_mapping = GUITAR_MAPPING
        elif layout == "drums":
            self.current_mapping = DRUM_MAPPING
        else:
            self.current_mapping = KEYBOARD_MAPPING
        self.input_handler = InputHandler(self.current_mapping, dry_run=dry_run)
        self.running = False
        self.active_notes: dict[int, int] = {}
        self.guitar_sustain_extension = 0.1

    def start(self) -> None:
        try:
            mid = mido.MidiFile(self.midi_file)
        except FileNotFoundError:
            print(f"Error: File '{self.midi_file}' not found.")
            return

        # Auto-Transpose Logic
        if self.layout == "guitar":
            optimal_transpose = self._calculate_best_transpose(mid)
            if optimal_transpose != 0:
                print(
                    f"Auto-Transposing by +{optimal_transpose} semitones for best fit."
                )
                self.transpose += optimal_transpose

        print(f"Playing '{self.midi_file}'...")
        print(
            f"Speed: {self.speed}x, Transpose: {self.transpose} semitones, Layout: {self.layout}"
        )
        print("Press Ctrl+C to stop.")

        print("Starting in 3 seconds... Switch to your game window NOW!")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        self.running = True
        try:
            for msg in mid:
                if not self.running:
                    break

                if not hasattr(msg, "time"):
                    continue

                # Retrieve message time and sleep if needed
                time_to_wait = msg.time / self.speed
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

                if getattr(msg, "is_meta", False):
                    continue

                if msg.type in ["note_on", "note_off"]:
                    if isinstance(msg, Message):
                        self._handle_note_msg(msg)

        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.stop()

    def _calculate_best_transpose(self, mid: mido.MidiFile) -> int:
        """Calculates the transposition that maximizes diatonic (white key) notes."""
        # Valid pitch classes for C Major / A Minor (White Keys)
        # C, D, E, F, G, A, B -> 0, 2, 4, 5, 7, 9, 11
        VALID_CLASSES = {0, 2, 4, 5, 7, 9, 11}

        pitch_counts = {i: 0 for i in range(12)}
        total_notes = 0

        for track in mid.tracks:
            for msg in track:
                if msg.type == "note_on" and msg.velocity > 0:
                    total_notes += 1
                    pitch_counts[msg.note % 12] += 1

        if total_notes == 0:
            return 0

        best_transpose = 0
        best_hits = -1

        for t in range(12):
            hits = 0
            for pitch, count in pitch_counts.items():
                shifted = (pitch + t) % 12
                if shifted in VALID_CLASSES:
                    hits += count

            if hits > best_hits:
                best_hits = hits
                best_transpose = t

        # If the best transpose is just 0 (or equivalent 12), return 0
        # If it improves coverage effectively, return it.
        # Check current coverage
        current_hits = 0
        for pitch, count in pitch_counts.items():
            if pitch in VALID_CLASSES:
                current_hits += count

        if best_hits > current_hits:
            # Normalize to -6 to +5 range for cleaner output?
            # Or just 0-11. Let's keep 0-11 as positive shift.
            return best_transpose

        return 0

    def _handle_note_msg(self, msg: Message) -> None:
        note_val = msg.note
        velocity = msg.velocity
        msg_type = msg.type

        note = note_val + self.transpose

        if self.layout == "keyboard":
            self._handle_keyboard_layout(note, velocity, msg_type)
        elif self.layout == "guitar":
            self._handle_guitar_layout(note, velocity, msg_type)
        elif self.layout == "drums":
            self._handle_drum_layout(note, velocity, msg_type)

    def _handle_keyboard_layout(self, note: int, velocity: int, msg_type: str) -> None:
        # Keyboard Logic: Fire-and-Forget for Note On
        if msg_type == "note_on" and velocity > 0:
            # Fold note to fit in Keyboard range (C3-C6 -> 48-84)
            effective_note = self._fold_note(note, 48, 84)

            if effective_note in self.current_mapping:
                key_code = self.current_mapping[effective_note]
                key_name = get_key_name(key_code)
                print(f"Note {note} (Folded to {effective_note}) -> Key '{key_name}'")

                # Asynchronous press to not block MIDI processing
                t = threading.Thread(
                    target=self.input_handler.press, args=(key_code, 0.1)
                )
                t.daemon = True
                t.start()

    def _handle_guitar_layout(self, note: int, velocity: int, msg_type: str) -> None:
        # Guitar Logic: Fold note to fit in Guitar range (C4-C6 -> 60-84)
        effective_note = self._fold_note(note, 60, 84)
        original_note = note

        # Guitar Mode Tap Logic: Fire-and-forget, ignore note_off
        if msg_type == "note_on" and velocity > 0:
            if effective_note in self.current_mapping:
                key_code = self.current_mapping[effective_note]
                key_name = get_key_name(key_code)
                print(
                    f"Note ON {original_note} (Folded to {effective_note}) -> Key '{key_name}'"
                )

                t = threading.Thread(
                    target=self.input_handler.press, args=(key_code, 0.1)
                )
                t.daemon = True
                t.start()

    def _handle_drum_layout(self, note: int, velocity: int, msg_type: str) -> None:
        # Drum Logic: Direct mapping, no folding, fire-and-forget
        if msg_type == "note_on" and velocity > 0:
            if note in self.current_mapping:
                key_code = self.current_mapping[note]
                key_name = get_key_name(key_code)
                print(f"Drum Hit {note} -> Key '{key_name}'")

                t = threading.Thread(
                    target=self.input_handler.press, args=(key_code, 0.1)
                )
                t.daemon = True
                t.start()

    def _fold_note(self, note: int, min_val: int, max_val: int) -> int:
        """Shifts note by octaves until it fits within [min_val, max_val]."""
        # Shift up if too low
        while note < min_val:
            note += 12
        # Shift down if too high
        while note > max_val:
            note -= 12
        return note

    def _release_key_delayed(self, key_code: int, delay: float, note: int) -> None:
        time.sleep(delay)
        self.input_handler.key_up(key_code)
        print(f"Note OFF {note} -> Key '{get_key_name(key_code)}' (Released)")

    def stop(self) -> None:
        self.running = False
        print("Releasing all keys...")
        self.input_handler.cleanup()
        print("Done.")
