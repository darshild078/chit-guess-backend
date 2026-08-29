import enum

class RoomStatus(str, enum.Enum):
    lobby = "lobby"
    waiting = "waiting"
    submissions_open = "submissions_open"
    submissions_closed = "submissions_closed"
    guessing = "guessing"
    revealed = "revealed"
    completed = "completed"
    ended = "ended"

class RoundStatus(str, enum.Enum):
    waiting = "waiting"
    submissions_open = "submissions_open"
    submissions_closed = "submissions_closed"
    guessing = "guessing"
    revealed = "revealed"
    completed = "completed"

class ParticipantRole(str, enum.Enum):
    owner = "owner"
    player = "player"
