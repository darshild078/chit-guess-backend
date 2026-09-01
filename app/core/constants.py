from enum import Enum

class GameMode(str, Enum):
    confessions = "confessions"
    chameleon = "chameleon"
    roasts = "roasts"

class PromptCategory(str, Enum):
    general = "general"
    school = "school"
    embarrassing = "embarrassing"
    spicy = "spicy"
    pleasures = "pleasures"
    custom = "custom"

class RoomStatus(str, Enum):
    lobby = "lobby"
    waiting = "waiting"
    submissions_open = "submissions_open"
    submissions_closed = "submissions_closed"
    guessing = "guessing"
    revealed = "revealed"
    completed = "completed"
    ended = "ended"

class RoundStatus(str, Enum):
    waiting = "waiting"
    submissions_open = "submissions_open"
    submissions_closed = "submissions_closed"
    guessing = "guessing"
    revealed = "revealed"
    completed = "completed"

class ParticipantRole(str, Enum):
    owner = "owner"
    player = "player"

# Scoring values
SCORE_CORRECT_GUESS: int = 100
SCORE_DOUBLE_DOWN_WIN: int = 200
SCORE_DOUBLE_DOWN_LOSS: int = 50
SCORE_STEALTH_BONUS: int = 150
SCORE_CHAMELEON_ESCAPE: int = 200
SCORE_CHAMELEON_STEAL: int = 150
SCORE_ROAST_VOTE: int = 100
SCORE_ROAST_TOP_BONUS: int = 100

# Limits and Configuration
ROOM_CODE_LENGTH: int = 6
ALLOWED_ROOM_CHARS: str = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DEFAULT_MAX_PLAYERS: int = 10
MIN_PLAYERS: int = 2
MAX_PLAYERS: int = 30
DEFAULT_TOTAL_ROUNDS: int = 3
MIN_ROUNDS: int = 1
MAX_ROUNDS: int = 10
DEFAULT_TIMER_SECONDS: int = 60
ROOM_EXPIRY_HOURS: int = 24
MIN_DISPLAY_NAME_LEN: int = 2
MAX_DISPLAY_NAME_LEN: int = 20
MAX_CHIT_LENGTH: int = 150
