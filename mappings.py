try:
    from evdev import ecodes as e
except ImportError:
    e = None

# --- Key Mapping Configuration ---


# Default to 0 if evdev is not present (for analysis/testing on non-linux)
# This keeps the map definition valid but useless for playing
def k(name: str) -> int:
    if e:
        return getattr(e, name, 0)
    return 0


KEYBOARD_MAPPING: dict[int, int] = {
    # Low Octave (C3-B3)
    48: k("KEY_COMMA"),  # C3
    49: k("KEY_L"),  # C#3
    50: k("KEY_DOT"),  # D3
    51: k("KEY_SLASH"),  # D#3
    52: k("KEY_SEMICOLON"),  # E3
    53: k("KEY_O"),  # F3
    54: k("KEY_0"),  # F#3
    55: k("KEY_P"),  # G3
    56: k("KEY_MINUS"),  # G#3
    57: k("KEY_RIGHTBRACE"),  # A3
    58: k("KEY_EQUAL"),  # A#3
    59: k("KEY_LEFTBRACE"),  # B3
    # Mid Octave (C4-B4)
    60: k("KEY_Z"),  # C4
    61: k("KEY_S"),  # C#4
    62: k("KEY_X"),  # D4
    63: k("KEY_D"),  # D#4
    64: k("KEY_C"),  # E4
    65: k("KEY_V"),  # F4
    66: k("KEY_G"),  # F#4
    67: k("KEY_B"),  # G4
    68: k("KEY_H"),  # G#4
    69: k("KEY_N"),  # A4
    70: k("KEY_J"),  # A#4
    71: k("KEY_M"),  # B4
    # High Octave (C5-B5)
    72: k("KEY_Q"),  # C5
    73: k("KEY_2"),  # C#5
    74: k("KEY_W"),  # D5
    75: k("KEY_3"),  # D#5
    76: k("KEY_E"),  # E5
    77: k("KEY_R"),  # F5
    78: k("KEY_5"),  # F#5
    79: k("KEY_T"),  # G5
    80: k("KEY_6"),  # G#5
    81: k("KEY_Y"),  # A5
    82: k("KEY_7"),  # A#5
    83: k("KEY_U"),  # B5
    # Highest Do (C6)
    84: k("KEY_I"),  # C6
}

GUITAR_MAPPING: dict[int, int] = {
    # Low Octave (C4-B4) -> Bottom Row (A-J)
    60: k("KEY_A"),  # Do (C4)
    62: k("KEY_S"),  # Re (D4)
    64: k("KEY_D"),  # Mi (E4)
    65: k("KEY_F"),  # Fa (F4)
    67: k("KEY_G"),  # Sol (G4)
    69: k("KEY_H"),  # La (A4)
    71: k("KEY_J"),  # Ti (B4)
    # High Octave (C5-C6) -> Top Row (Q-I)
    72: k("KEY_Q"),  # Do (C5)
    74: k("KEY_W"),  # Re (D5)
    76: k("KEY_E"),  # Mi (E5)
    77: k("KEY_R"),  # Fa (F5)
    79: k("KEY_T"),  # Sol (G5)
    81: k("KEY_Y"),  # La (A5)
    83: k("KEY_U"),  # Ti (B5)
    84: k("KEY_I"),  # Do (C6)
}


DRUM_MAPPING: dict[int, int] = {
    # Kick (Bass Drum) -> H
    35: k("KEY_H"),  # Acoustic Bass Drum
    36: k("KEY_H"),  # Bass Drum 1
    # Snare -> J
    38: k("KEY_J"),  # Acoustic Snare
    40: k("KEY_J"),  # Electric Snare
    # Hi-Hats -> K (Closed), L (Open/Pedal)
    42: k("KEY_K"),  # Closed Hi-Hat
    44: k("KEY_L"),  # Pedal Hi-Hat
    46: k("KEY_L"),  # Open Hi-Hat
    # Toms -> Y (Low), U (Mid), I (High)
    41: k("KEY_Y"),  # Low Floor Tom
    43: k("KEY_Y"),  # High Floor Tom
    45: k("KEY_U"),  # Low Tom
    47: k("KEY_U"),  # Low-Mid Tom
    48: k("KEY_I"),  # Hi-Mid Tom
    50: k("KEY_I"),  # High Tom
    # Cymbals -> O
    49: k("KEY_O"),  # Crash Cymbal 1
    51: k("KEY_O"),  # Ride Cymbal 1
    52: k("KEY_O"),  # Chinese Cymbal
    53: k("KEY_O"),  # Ride Bell
    55: k("KEY_O"),  # Splash Cymbal
    57: k("KEY_O"),  # Crash Cymbal 2
    59: k("KEY_O"),  # Ride Cymbal 2
}


KEY_NAMES: dict[int, str] = {}
if e:
    KEY_NAMES = {v: n for n, v in e.ecodes.items() if isinstance(v, int)}


def get_key_name(key_code: int) -> str:
    return KEY_NAMES.get(key_code, str(key_code))
