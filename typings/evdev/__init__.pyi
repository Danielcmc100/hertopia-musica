from typing import Any, Dict, Sequence

class ecodes:
    EV_KEY: int
    KEY_A: int
    KEY_B: int
    KEY_C: int
    KEY_D: int
    KEY_E: int
    KEY_F: int
    KEY_G: int
    KEY_H: int
    KEY_I: int
    KEY_J: int
    KEY_K: int
    KEY_L: int
    KEY_M: int
    KEY_N: int
    KEY_O: int
    KEY_P: int
    KEY_Q: int
    KEY_R: int
    KEY_S: int
    KEY_T: int
    KEY_U: int
    KEY_V: int
    KEY_W: int
    KEY_X: int
    KEY_Y: int
    KEY_Z: int
    KEY_1: int
    KEY_2: int
    KEY_3: int
    KEY_4: int
    KEY_5: int
    KEY_6: int
    KEY_7: int
    KEY_8: int
    KEY_9: int
    KEY_0: int
    KEY_MINUS: int
    KEY_EQUAL: int
    KEY_LEFTBRACE: int
    KEY_RIGHTBRACE: int
    KEY_SEMICOLON: int
    KEY_APOSTROPHE: int
    KEY_GRAVE: int
    KEY_BACKSLASH: int
    KEY_COMMA: int
    KEY_DOT: int
    KEY_SLASH: int
    ecodes: Dict[str, int]

class UInput:
    def __init__(
        self,
        events: Dict[int, Sequence[int]] | None = None,
        name: str = ...,
        vendor: int = ...,
        product: int = ...,
        version: int = ...,
        bustype: int = ...,
    ) -> None: ...
    def write(self, etype: int, code: int, value: int) -> None: ...
    def syn(self) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) -> "UInput": ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...
