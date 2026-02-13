import sys

import mido


def analyze(file_path):
    try:
        mid = mido.MidiFile(file_path)
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    notes = []

    print(f"--- Analyzing {file_path} ---")
    for msg in mid:
        if msg.type == "note_on" and msg.velocity > 0:
            notes.append(msg.note)

    if not notes:
        print("No notes found!")
        return

    min_note = min(notes)
    max_note = max(notes)
    avg_note = sum(notes) / len(notes)
    print(f"Average Note: {avg_note:.2f}")

    print(f"Total Notes: {len(notes)}")
    print(
        f"Lowest Note: {min_note} ({mido.format_as_string(mido.Message('note_on', note=min_note))})"
    )
    print(
        f"Highest Note: {max_note} ({mido.format_as_string(mido.Message('note_on', note=max_note))})"
    )

    # Check overlap with our mapping (48 to 84)
    mapped_count = sum(1 for n in notes if 48 <= n <= 84)
    print(
        f"Notes in mapped range (48-84): {mapped_count} ({mapped_count / len(notes) * 100:.1f}%)"
    )

    # Suggest transposition
    # We want to maximize overlap with 48-84
    # Simple brute force optimal shift
    best_shift = 0
    best_coverage = 0

    # Check shifts from -24 to +24
    for shift in range(-36, 36):
        count = sum(1 for n in notes if 48 <= (n + shift) <= 84)
        if count > best_coverage:
            best_coverage = count
            best_shift = shift

    print(
        f"Suggested Transpose: {best_shift} (Coverage: {best_coverage / len(notes) * 100:.1f}%)"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_midi.py <file.mid>")
    else:
        analyze(sys.argv[1])
