from typing import IO, Any, Iterator, List, Optional, Union

class Message:
    type: str
    time: float
    note: int
    velocity: int
    channel: int
    def __init__(self, type: str, **kwargs: Any) -> None: ...
    def copy(self, **kwargs: Any) -> "Message": ...

def format_as_string(msg: Message, include_time: bool = True) -> str: ...

class MetaMessage(Message):
    is_meta: bool

class MidiTrack(List[Union[Message, MetaMessage]]):
    def __init__(self) -> None: ...
    def append(self, object: Union[Message, MetaMessage]) -> None: ...

class MidiFile:
    tracks: List[MidiTrack]
    filename: Optional[str]
    type: int
    ticks_per_beat: int

    def __init__(
        self, filename: Optional[str | IO[bytes]] = None, **kwargs: Any
    ) -> None: ...
    def save(self, filename: Optional[str | IO[bytes]] = None) -> None: ...
    def __iter__(self) -> Iterator[Union[Message, MetaMessage]]: ...
    def play(
        self, meta_messages: bool = False
    ) -> Iterator[Union[Message, MetaMessage]]: ...
    @property
    def length(self) -> float: ...
