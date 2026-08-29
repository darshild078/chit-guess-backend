import pytest
from app.utils.sanitize import sanitize_single_word, sanitize_display_name
from app.errors import AppError

def test_sanitize_display_name_valid():
    assert sanitize_display_name("  Arthur  ") == "Arthur"
    assert sanitize_display_name("Sadie Adler") == "Sadie Adler"

def test_sanitize_display_name_invalid():
    with pytest.raises(AppError):
        sanitize_display_name("A")
    with pytest.raises(AppError):
        sanitize_display_name("ThisNameIsWayTooLongForAChitGuessPlayerName")

def test_sanitize_single_word_valid():
    assert sanitize_single_word("  Galaxy  ") == "Galaxy"
    assert sanitize_single_word("apple") == "apple"
    assert sanitize_single_word("SUPERHERO") == "SUPERHERO"

def test_sanitize_single_word_invalid():
    with pytest.raises(AppError):
        sanitize_single_word("")
    with pytest.raises(AppError):
        sanitize_single_word("Two Words")
    with pytest.raises(AppError):
        sanitize_single_word("Word123")
    with pytest.raises(AppError):
        sanitize_single_word("hello!")
