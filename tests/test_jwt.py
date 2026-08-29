import pytest
from app.utils.jwt_helper import sign_participant_token, verify_participant_token
from app.errors import AppError

def test_jwt_sign_and_verify():
    token = sign_participant_token("part_123", "room_456", "owner", 1)
    payload = verify_participant_token(token)

    assert payload["participantId"] == "part_123"
    assert payload["roomId"] == "room_456"
    assert payload["role"] == "owner"
    assert payload["sessionVersion"] == 1

def test_jwt_invalid_token():
    with pytest.raises(AppError):
        verify_participant_token("invalid.token.string")
