"""
test_system_prompt.py
─────────────────────
Tests that the prompt builder injects context correctly
and includes all required schema sections.
"""

import pytest
from app.prompts.system_prompt import build_system_prompt


def test_prompt_includes_country_list():
    prompt = build_system_prompt(countries=["IN", "US", "KR"], providers=[])
    assert "IN" in prompt
    assert "US" in prompt
    assert "KR" in prompt


def test_prompt_includes_provider_list():
    prompt = build_system_prompt(countries=[], providers=["Sony", "Viacom"])
    assert "Sony" in prompt
    assert "Viacom" in prompt


def test_prompt_includes_all_status_values():
    prompt = build_system_prompt(countries=[], providers=[])
    for status in ["Ready For QC", "QC Fail", "Released", "Revoked", "Untrackable"]:
        assert status in prompt, f"Missing status: {status}"


def test_prompt_includes_all_content_types():
    prompt = build_system_prompt(countries=[], providers=[])
    for content_type in ["EPISODE", "MOVIE", "SINGLEVOD", "MUSIC", "SHOW", "SEASON"]:
        assert content_type in prompt, f"Missing content type: {content_type}"


def test_prompt_includes_output_schema():
    prompt = build_system_prompt(countries=[], providers=[])
    assert '"status": "resolved"' in prompt
    assert '"status": "ambiguous"' in prompt
    assert '"status": "error"' in prompt


def test_prompt_includes_few_shot_examples():
    prompt = build_system_prompt(countries=[], providers=[])
    assert "Mirzapur" in prompt  # From few-shot examples


def test_empty_context_shows_placeholder():
    prompt = build_system_prompt(countries=[], providers=[])
    assert "Not provided" in prompt


def test_prompt_is_string_and_nonempty():
    prompt = build_system_prompt(countries=["IN"], providers=["Sony"])
    assert isinstance(prompt, str)
    assert len(prompt) > 500
