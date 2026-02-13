from mido import Message, MidiFile, MidiTrack

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

track.append(Message("program_change", program=12, time=0))
track.append(Message("note_on", note=60, velocity=64, time=32))
track.append(Message("note_off", note=60, velocity=64, time=32))

mid.save("debug_test.mid")
print("Created debug_test.mid")
