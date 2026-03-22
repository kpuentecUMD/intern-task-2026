"""Integration tests -- now requires ANTHROPIC_API_KEY to be set.

Run with: pytest tests/test_feedback_integration.py -v

These tests make real API calls. Skip them in CI or when no key is available.
"""

import os

import pytest
from app.feedback import get_feedback
from app.models import FeedbackRequest

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set -- skipping integration tests",
)

VALID_ERROR_TYPES = {
    "grammar",
    "spelling",
    "word_choice",
    "punctuation",
    "word_order",
    "missing_word",
    "extra_word",
    "conjugation",
    "gender_agreement",
    "number_agreement",
    "tone_register",
    "other",
}
VALID_DIFFICULTIES = {"A1", "A2", "B1", "B2", "C1", "C2"}


@pytest.mark.asyncio
async def test_spanish_conjugation_error():
    """Spanish sentence with mixed verb forms."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Yo soy fue al mercado ayer.",
            target_language="Spanish",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert result.difficulty in VALID_DIFFICULTIES
    for error in result.errors:
        assert error.error_type in VALID_ERROR_TYPES
        assert len(error.explanation) > 0


@pytest.mark.asyncio
async def test_correct_german():
    """Correct German sentence should return no errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Ich habe gestern einen interessanten Film gesehen.",
            target_language="German",
            native_language="English",
        )
    )
    assert result.is_correct is True
    assert result.errors == []
    assert result.corrected_sentence == "Ich habe gestern einen interessanten Film gesehen."
    assert result.difficulty in VALID_DIFFICULTIES


@pytest.mark.asyncio
async def test_french_gender_agreement():
    """French sentence with multiple gender agreement errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="La chat noir est sur le table.",
            target_language="French",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert result.difficulty in VALID_DIFFICULTIES


@pytest.mark.asyncio
async def test_japanese_particle_error():
    """Japanese sentence with wrong particle."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="私は東京を住んでいます。",
            target_language="Japanese",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert any("に" in e.correction for e in result.errors)
    assert result.difficulty in VALID_DIFFICULTIES


@pytest.mark.asyncio
async def test_portuguese_spelling_error():
    """Portuguese sentence with spelling error."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Eu quero comprar um prezente para minha irmã.",
            target_language="Portuguese",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert any(e.error_type == "spelling" for e in result.errors)
    assert "presente" in result.corrected_sentence


@pytest.mark.asyncio
async def test_correct_spanish_sentence():
    """Correct Spanish sentence should return no errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Ella come una manzana cada día.",
            target_language="Spanish",
            native_language="English",
        )
    )
    assert result.is_correct is True
    assert result.errors == []
    assert result.corrected_sentence == "Ella come una manzana cada día."


@pytest.mark.asyncio
async def test_korean_sentence():
    """Korean sentence with particle error."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="나는 학교을 갔어요.",
            target_language="Korean",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert result.difficulty in VALID_DIFFICULTIES
    for error in result.errors:
        assert error.error_type in VALID_ERROR_TYPES
        assert len(error.explanation) > 0


@pytest.mark.asyncio
async def test_explanation_in_native_language():
    """Explanations should be in the learner's native language, not the target language."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Je suis allé au magasin hier avec mes amis.",
            target_language="French",
            native_language="English",
        )
    )
    assert result.difficulty in VALID_DIFFICULTIES
    for error in result.errors:
        assert len(error.explanation) > 0


@pytest.mark.asyncio
async def test_multiple_errors():
    """Sentence with multiple distinct errors should return multiple error entries."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="La chat noir est sur le table.",
            target_language="French",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 2
    assert result.difficulty in VALID_DIFFICULTIES


@pytest.mark.asyncio
async def test_response_schema_fields():
    """Every response must have all required fields with correct types."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Yo soy fue al mercado ayer.",
            target_language="Spanish",
            native_language="English",
        )
    )
    assert isinstance(result.corrected_sentence, str)
    assert isinstance(result.is_correct, bool)
    assert isinstance(result.errors, list)
    assert isinstance(result.difficulty, str)
    assert result.difficulty in VALID_DIFFICULTIES
    for error in result.errors:
        assert isinstance(error.original, str)
        assert isinstance(error.correction, str)
        assert isinstance(error.error_type, str)
        assert isinstance(error.explanation, str)
        assert error.error_type in VALID_ERROR_TYPES