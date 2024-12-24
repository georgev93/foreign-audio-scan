from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SubtitleSegment:
    start_time: float  # in seconds
    end_time: float  # in seconds
    duration: float  # in seconds
    text: str


@dataclass
class SubtitleTrack:
    id: int
    codec: str
    language: str
    name: Optional[str] = None
