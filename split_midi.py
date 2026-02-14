import os
import sys

import mido

# General MIDI Instrument List
GM_INSTRUMENTS = {
    0: "Acoustic Grand Piano",
    1: "Bright Acoustic Piano",
    2: "Electric Grand Piano",
    3: "Honky-tonk Piano",
    4: "Electric Piano 1",
    5: "Electric Piano 2",
    6: "Harpsichord",
    7: "Clavinet",
    8: "Celesta",
    9: "Glockenspiel",
    10: "Music Box",
    11: "Vibraphone",
    12: "Marimba",
    13: "Xylophone",
    14: "Tubular Bells",
    15: "Dulcimer",
    16: "Drawbar Organ",
    17: "Percussive Organ",
    18: "Rock Organ",
    19: "Church Organ",
    20: "Reed Organ",
    21: "Accordion",
    22: "Harmonica",
    23: "Tango Accordion",
    24: "Acoustic Guitar (nylon)",
    25: "Acoustic Guitar (steel)",
    26: "Electric Guitar (jazz)",
    27: "Electric Guitar (clean)",
    28: "Electric Guitar (muted)",
    29: "Overdriven Guitar",
    30: "Distortion Guitar",
    31: "Guitar Harmonics",
    32: "Acoustic Bass",
    33: "Electric Bass (finger)",
    34: "Electric Bass (pick)",
    35: "Fretless Bass",
    36: "Slap Bass 1",
    37: "Slap Bass 2",
    38: "Synth Bass 1",
    39: "Synth Bass 2",
    40: "Violin",
    41: "Viola",
    42: "Cello",
    43: "Contrabass",
    44: "Tremolo Strings",
    45: "Pizzicato Strings",
    46: "Orchestral Harp",
    47: "Timpani",
    48: "String Ensemble 1",
    49: "String Ensemble 2",
    50: "SynthStrings 1",
    51: "SynthStrings 2",
    52: "Choir Aahs",
    53: "Voice Oohs",
    54: "Synth Voice",
    55: "Orchestra Hit",
    56: "Trumpet",
    57: "Trombone",
    58: "Tuba",
    59: "Muted Trumpet",
    60: "French Horn",
    61: "Brass Section",
    62: "SynthBrass 1",
    63: "SynthBrass 2",
    64: "Soprano Sax",
    65: "Alto Sax",
    66: "Tenor Sax",
    67: "Baritone Sax",
    68: "Oboe",
    69: "English Horn",
    70: "Bassoon",
    71: "Clarinet",
    72: "Piccolo",
    73: "Flute",
    74: "Recorder",
    75: "Pan Flute",
    76: "Blown Bottle",
    77: "Shakuhachi",
    78: "Whistle",
    79: "Ocarina",
    80: "Lead 1 (square)",
    81: "Lead 2 (sawtooth)",
    82: "Lead 3 (calliope)",
    83: "Lead 4 (chiff)",
    84: "Lead 5 (charang)",
    85: "Lead 6 (voice)",
    86: "Lead 7 (fifths)",
    87: "Lead 8 (bass + lead)",
    88: "Pad 1 (new age)",
    89: "Pad 2 (warm)",
    90: "Pad 3 (polysynth)",
    91: "Pad 4 (choir)",
    92: "Pad 5 (bowed)",
    93: "Pad 6 (metallic)",
    94: "Pad 7 (halo)",
    95: "Pad 8 (sweep)",
    96: "FX 1 (rain)",
    97: "FX 2 (soundtrack)",
    98: "FX 3 (crystal)",
    99: "FX 4 (atmosphere)",
    100: "FX 5 (brightness)",
    101: "FX 6 (goblins)",
    102: "FX 7 (echoes)",
    103: "FX 8 (sci-fi)",
    104: "Sitar",
    105: "Banjo",
    106: "Shamisen",
    107: "Koto",
    108: "Kalimba",
    109: "Bag pipe",
    110: "Fiddle",
    111: "Shanai",
    112: "Tinkle Bell",
    113: "Agogo",
    114: "Steel Drums",
    115: "Woodblock",
    116: "Taiko Drum",
    117: "Melodic Tom",
    118: "Synth Drum",
    119: "Reverse Cymbal",
    120: "Guitar Fret Noise",
    121: "Breath Noise",
    122: "Seashore",
    123: "Bird Tweet",
    124: "Telephone Ring",
    125: "Helicopter",
    126: "Applause",
    127: "Gunshot",
}


def split_midi_by_channel(file_path):
    try:
        mid = mido.MidiFile(file_path)
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return

    print(f"Analyzing {file_path} for channels...")

    # Find all unique channels used in the MIDI file
    used_channels = set()
    for track in mid.tracks:
        for msg in track:
            if not msg.is_meta and hasattr(msg, "channel"):
                used_channels.add(msg.channel)

    if not used_channels:
        print("No channels found in MIDI file.")
        return

    print(f"Found channels: {sorted(list(used_channels))}")

    # Create output directory
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join(os.path.dirname(file_path), f"{base_name}_split")
    os.makedirs(output_dir, exist_ok=True)

    for channel in used_channels:
        new_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)

        has_notes = False
        program_found = None

        for track in mid.tracks:
            new_track = mido.MidiTrack()
            accumulated_time = 0

            for msg in track:
                dt = msg.time

                # Keep meta messages
                if msg.is_meta:
                    new_msg = msg.copy()
                    new_msg.time += accumulated_time
                    new_track.append(new_msg)
                    accumulated_time = 0

                # Keep messages for the current channel
                elif hasattr(msg, "channel") and msg.channel == channel:
                    new_msg = msg.copy()
                    new_msg.time += accumulated_time
                    new_track.append(new_msg)
                    accumulated_time = 0
                    if msg.type == "note_on" or msg.type == "note_off":
                        has_notes = True
                    if msg.type == "program_change":
                        program_found = msg.program
                # Keep messages without channel attribute (rare, but possible like sysex if not meta)
                elif not hasattr(msg, "channel"):
                    # Usually sysex are treated as distinct by mido, let's include them?
                    # Sysex usually global.
                    new_msg = msg.copy()
                    new_msg.time += accumulated_time
                    new_track.append(new_msg)
                    accumulated_time = 0
                else:
                    # Skip other channels, accumulate time
                    accumulated_time += dt

            # Only add track if it has meaningful content?
            # Actually, standard practice is to keep track 0 for meta even if empty of notes.
            # But let's add it regardless if it's not empty.
            if len(new_track) > 0:
                new_mid.tracks.append(new_track)

        # Save file
        if has_notes:
            instrument_name = f"Channel_{channel + 1}"

            if channel == 9:  # MIDI channel 10 is typically drums (0-indexed)
                instrument_name = "Drums"
            elif program_found is not None:
                instrument_name = GM_INSTRUMENTS.get(
                    program_found, f"Program_{program_found}"
                )
                # Clean up filename (remove spaces, etc if needed, or keep spaces)
                instrument_name = (
                    instrument_name.replace(" ", "_")
                    .replace("/", "-")
                    .replace("(", "")
                    .replace(")", "")
                )

            out_filename = os.path.join(
                output_dir, f"{base_name}_{instrument_name}.mid"
            )

            # Handle duplicates if multiple channels use same instrument
            counter = 1
            while os.path.exists(out_filename):
                out_filename = os.path.join(
                    output_dir, f"{base_name}_{instrument_name}_{counter}.mid"
                )
                counter += 1

            new_mid.save(out_filename)
            print(f"Saved: {out_filename}")
        else:
            print(f"Channel {channel + 1} has no notes, skipping.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_midi.py <file.mid>")
    else:
        split_midi_by_channel(sys.argv[1])
