from mido import Message, MidiFile, MidiTrack

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

# Full mapped range: Low C (48) to High C (84)
start_note = 48
end_note = 84

print(f"Generating MIDI with notes from {start_note} to {end_note}...")

for note in range(start_note, end_note + 1):
    # Add note_on
    track.append(
        Message("note_on", note=note, velocity=64, time=200)
    )  # 200 ticks delay
    # Add note_off
    track.append(Message("note_off", note=note, velocity=64, time=200))

output_file = "/home/daniel/projects/hertopia-musica/test_all_keys.mid"
mid.save(output_file)
print(f"Created {output_file}")
