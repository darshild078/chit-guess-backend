import pytest
from app.utils.cuid import generate_cuid
from app.core.security import sign_participant_token, verify_participant_token

def test_token_creation():
    token = sign_participant_token("p1", "r1", "player", 1)
    payload = verify_participant_token(token)
    assert payload["participantId"] == "p1"
    assert payload["roomId"] == "r1"
    assert payload["role"] == "player"

def test_generate_cuid_uniqueness():
    ids = {generate_cuid() for _ in range(100)}
    assert len(ids) == 100
