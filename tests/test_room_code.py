from app.utils.room_code import generate_room_code, is_valid_room_code

def test_generate_room_code():
    code = generate_room_code()
    assert len(code) == 6
    assert is_valid_room_code(code)

def test_is_valid_room_code():
    assert is_valid_room_code("ABCDEF")
    assert not is_valid_room_code("ABCD")
    assert not is_valid_room_code("ABCDE0")  # '0' is excluded
    assert not is_valid_room_code("ABCDEO")  # 'O' is excluded
    assert not is_valid_room_code("ABCDE1")  # '1' is excluded
    assert not is_valid_room_code("ABCDEI")  # 'I' is excluded
