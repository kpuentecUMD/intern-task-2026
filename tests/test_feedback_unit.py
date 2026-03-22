"""Unit tests -- run without an API key using mocked LLM responses."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.feedback import get_feedback
from app.models import FeedbackRequest


def _mock_anthropic_response(response_data: dict) -> MagicMock:
    """Build a mock Anthropic message response."""
    content_block = MagicMock()
    content_block.text = json.dumps(response_data)
    response = MagicMock()
    response.content = [content_block]
    return response


@pytest.mark.asyncio
async def test_feedback_with_errors():
    mock_response = {
        "corrected_sentence": "Yo fui al mercado ayer.",
        "is_correct": False,
        "errors": [
            {
                "original": "soy fue",
                "correction": "fui",
                "error_type": "conjugation",
                "explanation": "You mixed two verb forms.",
            }
        ],
        "difficulty": "A2",
    }

    with patch("app.feedback.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(mock_response)
        )

        request = FeedbackRequest(
            sentence="Yo soy fue al mercado ayer.",
            target_language="Spanish",
            native_language="English",
        )
        result = await get_feedback(request)

    assert result.is_correct is False
    assert result.corrected_sentence == "Yo fui al mercado ayer."
    assert len(result.errors) == 1
    assert result.errors[0].error_type == "conjugation"
    assert result.difficulty == "A2"


@pytest.mark.asyncio
async def test_feedback_correct_sentence():
    mock_response = {
        "corrected_sentence": "Ich habe gestern einen interessanten Film gesehen.",
        "is_correct": True,
        "errors": [],
        "difficulty": "B1",
    }

    with patch("app.feedback.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(mock_response)
        )

        request = FeedbackRequest(
            sentence="Ich habe gestern einen interessanten Film gesehen.",
            target_language="German",
            native_language="English",
        )
        result = await get_feedback(request)

    assert result.is_correct is True
    assert result.errors == []
    assert result.corrected_sentence == request.sentence


@pytest.mark.asyncio
async def test_feedback_multiple_errors():
    mock_response = {
        "corrected_sentence": "Le chat noir est sur la table.",
        "is_correct": False,
        "errors": [
            {
                "original": "La chat",
                "correction": "Le chat",
                "error_type": "gender_agreement",
                "explanation": "'Chat' is masculine.",
            },
            {
                "original": "le table",
                "correction": "la table",
                "error_type": "gender_agreement",
                "explanation": "'Table' is feminine.",
            },
        ],
        "difficulty": "A1",
    }

    with patch("app.feedback.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(mock_response)
        )

        request = FeedbackRequest(
            sentence="La chat noir est sur le table.",
            target_language="French",
            native_language="English",
        )
        result = await get_feedback(request)

    assert result.is_correct is False
    assert len(result.errors) == 2
    assert all(e.error_type == "gender_agreement" for e in result.errors)


@pytest.mark.asyncio
async def test_feedback_non_latin_script():
    """Unit test for non-Latin script response handling."""
    mock_response = {
        "corrected_sentence": "私は東京に住んでいます。",
        "is_correct": False,
        "errors": [
            {
                "original": "を",
                "correction": "に",
                "error_type": "grammar",
                "explanation": "The verb 'to live' requires the particle に not を.",
            }
        ],
        "difficulty": "A2",
    }

    with patch("app.feedback.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(mock_response)
        )

        request = FeedbackRequest(
            sentence="私は東京を住んでいます。",
            target_language="Japanese",
            native_language="English",
        )
        result = await get_feedback(request)

    assert result.is_correct is False
    assert len(result.errors) == 1
    assert result.errors[0].error_type == "grammar"


@pytest.mark.asyncio
async def test_feedback_empty_errors_when_correct():
    """Correct sentence must return empty errors list, not None."""
    mock_response = {
        "corrected_sentence": "Ella come una manzana cada día.",
        "is_correct": True,
        "errors": [],
        "difficulty": "A1",
    }

    with patch("app.feedback.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(mock_response)
        )

        request = FeedbackRequest(
            sentence="Ella come una manzana cada día.",
            target_language="Spanish",
            native_language="English",
        )
        result = await get_feedback(request)

    assert result.is_correct is True
    assert result.errors == []
    assert isinstance(result.errors, list)