import pytest
from app.data.prompt_packs import (
    get_random_confession_prompt,
    get_random_chameleon_round,
    get_random_roast_prompt,
)

def test_confession_prompts():
    prompt = get_random_confession_prompt("general")
    assert isinstance(prompt, str)
    assert len(prompt) > 5

    custom = get_random_confession_prompt(custom_prompt="What is your favorite secret?")
    assert custom == "What is your favorite secret?"

def test_chameleon_round():
    round_data = get_random_chameleon_round()
    assert "topic" in round_data
    assert "secretWord" in round_data
    assert "wordChoices" in round_data
    assert len(round_data["wordChoices"]) == 4
    assert round_data["secretWord"] in round_data["wordChoices"]

def test_roast_prompts():
    prompt = get_random_roast_prompt(["Alice", "Bob"])
    assert isinstance(prompt, str)
    assert ("Alice" in prompt or "Bob" in prompt)
