import argparse

from player import MidiPlayer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play MIDI files as game keystrokes.")

    parser.add_argument("file", help="Path to the MIDI file")  # pyright: ignore[reportUnusedCallResult]
    parser.add_argument(
        "--device-path",
        type=str,
        default=None,
        help="Path to a specific input device (e.g., /dev/input/eventX)",
    )
    parser.add_argument(
        "--speed", type=float, default=1.0, help="Playback speed (default: 1.0)"
    )
    parser.add_argument(
        "--transpose", type=int, default=0, help="Transpose semitones (default: 0)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print keys instead of pressing them"
    )
    parser.add_argument(
        "--layout",
        choices=["keyboard", "guitar", "drums"],
        default="keyboard",
        help="Control layout: 'keyboard' (default), 'guitar', or 'drums'",
    )

    parser.add_argument(
        "--id",
        type=int,
        default=None,
        help="Target instance ID. If not specified AND no --device-path, uses standard input (global).",
    )

    args = parser.parse_args()

    device_path = args.device_path

    # If device_path is NOT provided, check ID
    if device_path is None:
        if args.id is not None:
            # Try to read from .device_<ID> file
            device_file = f".device_{args.id}"
            try:
                with open(device_file, "r") as f:
                    device_path = f.read().strip()
                    print(
                        f"Auto-detected device path for Instance {args.id}: {device_path}"
                    )
            except FileNotFoundError:
                print(
                    f"Warning: Could not find '{device_file}'. Using standard global input."
                )
                pass
        else:
            # No ID and No Device Path -> Standard Input (Global UInput)
            print(
                "No instance ID or device path specified. Using standard global input."
            )
            pass

    player = MidiPlayer(
        midi_file=args.file,
        speed=args.speed,
        transpose=args.transpose,
        dry_run=args.dry_run,
        layout=args.layout,
        device_path=device_path,
    )

    player.start()
