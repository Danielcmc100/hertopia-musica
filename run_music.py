import argparse

from player import MidiPlayer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play MIDI files as game keystrokes.")

    parser.add_argument("file", help="Path to the MIDI file")  # pyright: ignore[reportUnusedCallResult]
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

    args = parser.parse_args()

    player = MidiPlayer(
        midi_file=args.file,
        speed=args.speed,
        transpose=args.transpose,
        dry_run=args.dry_run,
        layout=args.layout,
    )

    player.start()
