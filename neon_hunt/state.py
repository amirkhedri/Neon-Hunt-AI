from dataclasses import dataclass
from typing import FrozenSet, Tuple

Position = Tuple[int, int]

@dataclass(frozen=True)
class GameState:
    rows: int
    cols: int
    player: Position
    monster: Position
    exit: Position
    walls: FrozenSet[Position]
    turn: str = "player"
    turn_count: int = 0

    @staticmethod
    def from_level(level: dict) -> "GameState":
        return GameState(
            rows=level["rows"],
            cols=level["cols"],
            player=tuple(level["player"]),
            monster=tuple(level["monster"]),
            exit=tuple(level["exit"]),
            walls=frozenset(tuple(w) for w in level["walls"]),
            turn="player",
            turn_count=0,
        )
