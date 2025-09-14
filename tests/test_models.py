"""
Basic tests for SelfTUI Pydantic models.

This module contains unit tests for the core data models used throughout
SelfTUI, validating the Pydantic model behavior and validation rules.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import HttpUrl, ValidationError
from selftui.models import AIResponse, AppState, SearchResult, WebCard


class TestSearchResult:
    """Test cases for SearchResult model."""

    def test_valid_search_result(self):
        """Test creating a valid SearchResult."""
        result = SearchResult(
            title="Test Title",
            url=HttpUrl("https://example.com"),
            snippet="Test snippet content",
            source="duckduckgo",
            rank=0,
        )

        assert result.title == "Test Title"
        assert str(result.url) == "https://example.com/"
        assert result.snippet == "Test snippet content"
        assert result.source == "duckduckgo"
        assert result.rank == 0

    def test_title_validation(self):
        """Test title validation rules."""
        # Empty title should fail
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            SearchResult(title="", url=HttpUrl("https://example.com"))

        # Whitespace-only title should fail
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            SearchResult(title="   ", url=HttpUrl("https://example.com"))

    def test_title_truncation(self):
        """Test that very long titles are truncated."""
        long_title = "A" * 300
        result = SearchResult(title=long_title, url=HttpUrl("https://example.com"))

        assert len(result.title) <= 200

    def test_snippet_truncation(self):
        """Test that very long snippets are truncated."""
        long_snippet = "B" * 600
        result = SearchResult(
            title="Test", url=HttpUrl("https://example.com"), snippet=long_snippet
        )

        assert len(result.snippet) <= 500


class TestWebCard:
    """Test cases for WebCard model."""

    def test_valid_webcard(self):
        """Test creating a valid WebCard."""
        card = WebCard(
            title="Test Article",
            url=HttpUrl("https://example.com/article"),
            large_summary="This is a comprehensive summary of the article content.",
            dates=["2024-01-15"],
            facts=["Fact 1", "Fact 2"],
            links=["https://related.com"],
            content_length=1500,
            analysis_confidence=0.85,
        )

        assert card.title == "Test Article"
        assert str(card.url) == "https://example.com/article"
        assert "comprehensive summary" in card.large_summary
        assert len(card.facts) == 2
        assert len(card.dates) == 1
        assert len(card.links) == 1
        assert card.analysis_confidence == 0.85

    def test_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            WebCard()  # Missing required fields

    def test_summary_validation(self):
        """Test summary validation rules."""
        # Empty summary should fail
        with pytest.raises(ValidationError, match="Summary cannot be empty"):
            WebCard(title="Test", url=HttpUrl("https://example.com"), large_summary="")

        # Very short summary should fail
        with pytest.raises(ValidationError, match="Summary too short"):
            WebCard(
                title="Test", url=HttpUrl("https://example.com"), large_summary="Short"
            )

    def test_facts_validation(self):
        """Test facts list validation."""
        card = WebCard(
            title="Test",
            url=HttpUrl("https://example.com"),
            large_summary="This is a valid summary with enough content.",
            facts=["", "Valid fact", "  ", "Another valid fact", ""],
        )

        # Should filter out empty facts
        assert len(card.facts) == 2
        assert "Valid fact" in card.facts
        assert "Another valid fact" in card.facts

    def test_links_validation(self):
        """Test links validation."""
        card = WebCard(
            title="Test",
            url=HttpUrl("https://example.com"),
            large_summary="This is a valid summary with enough content.",
            links=[
                "https://valid.com",
                "invalid-url",
                "http://also-valid.com",
                "ftp://invalid-scheme.com",
                "",
            ],
        )

        # Should only keep valid HTTP/HTTPS URLs
        assert len(card.links) == 2
        assert "https://valid.com" in card.links
        assert "http://also-valid.com" in card.links

    def test_confidence_bounds(self):
        """Test analysis confidence bounds."""
        # Valid confidence
        card = WebCard(
            title="Test",
            url=HttpUrl("https://example.com"),
            large_summary="This is a valid summary with enough content.",
            analysis_confidence=0.75,
        )
        assert card.analysis_confidence == 0.75

        # Out of bounds should fail
        with pytest.raises(ValidationError):
            WebCard(
                title="Test",
                url=HttpUrl("https://example.com"),
                large_summary="Valid summary content here.",
                analysis_confidence=1.5,  # > 1.0
            )

    def test_to_display_dict(self):
        """Test conversion to display dictionary."""
        card = WebCard(
            title="Test Article",
            url=HttpUrl("https://example.com"),
            large_summary="Test summary content.",
            facts=["Fact 1", "Fact 2"],
            dates=["2024-01-15"],
            links=["https://example.com"],
            analysis_confidence=0.9,
        )

        display_dict = card.to_display_dict()

        assert display_dict["title"] == "Test Article"
        assert display_dict["facts_count"] == 2
        assert display_dict["dates_count"] == 1
        assert display_dict["links_count"] == 1
        assert display_dict["confidence"] == "90.0%"

    def test_get_preview(self):
        """Test preview generation."""
        long_summary = "A" * 200
        card = WebCard(
            title="Test", url=HttpUrl("https://example.com"), large_summary=long_summary
        )

        preview = card.get_preview(max_length=100)
        assert len(preview) <= 100
        assert preview.endswith("...")


class TestAIResponse:
    """Test cases for AIResponse model."""

    def test_successful_response(self):
        """Test successful AI response."""
        card = WebCard(
            title="Test",
            url=HttpUrl("https://example.com"),
            large_summary="Test summary content for validation.",
        )

        response = AIResponse(
            success=True,
            content=card,
            model_used="gemini-pro",
            processing_time=2.5,
            tokens_used=150,
        )

        assert response.success is True
        assert response.content == card
        assert response.model_used == "gemini-pro"
        assert response.processing_time == 2.5
        assert response.tokens_used == 150
        assert response.error_message == ""

    def test_failed_response(self):
        """Test failed AI response."""
        response = AIResponse(
            success=False, error_message="API key invalid", model_used="gemini-pro"
        )

        assert response.success is False
        assert response.content is None
        assert response.error_message == "API key invalid"

    def test_response_validation(self):
        """Test response state validation."""
        # Successful response must have content
        with pytest.raises(
            ValidationError, match="Successful response must include content"
        ):
            AIResponse(success=True, content=None, model_used="gemini-pro")

        # Failed response must have error message
        with pytest.raises(
            ValidationError, match="Failed response must include error message"
        ):
            AIResponse(success=False, error_message="", model_used="gemini-pro")

    def test_to_summary_dict(self):
        """Test conversion to summary dictionary."""
        response = AIResponse(
            success=True,
            content=WebCard(
                title="Test",
                url=HttpUrl("https://example.com"),
                large_summary="Test content for validation.",
            ),
            model_used="gemini-pro",
            processing_time=1.23,
            tokens_used=456,
        )

        summary = response.to_summary_dict()

        assert summary["success"] is True
        assert summary["model"] == "gemini-pro"
        assert summary["processing_time"] == "1.23s"
        assert summary["tokens_used"] == 456
        assert summary["error"] is None


class TestAppState:
    """Test cases for AppState model."""

    def test_initial_state(self):
        """Test initial application state."""
        state = AppState()

        assert state.api_key_set is False
        assert state.current_search_query == ""
        assert len(state.search_results) == 0
        assert len(state.active_cards) == 0
        assert state.last_error == ""
        assert isinstance(state.session_start, datetime)

    def test_add_search_results(self):
        """Test adding search results."""
        state = AppState()
        results = [
            SearchResult(title="Test 1", url=HttpUrl("https://example1.com")),
            SearchResult(title="Test 2", url=HttpUrl("https://example2.com")),
        ]

        state.add_search_results(results)

        assert len(state.search_results) == 2
        assert state.last_error == ""

    def test_add_web_card(self):
        """Test adding web cards."""
        state = AppState()
        card = WebCard(
            title="Test Card",
            url=HttpUrl("https://example.com"),
            large_summary="Test summary content.",
        )

        state.add_web_card(card)

        assert len(state.active_cards) == 1
        assert state.active_cards[0] == card
        assert state.last_error == ""

    def test_duplicate_url_handling(self):
        """Test that duplicate URLs replace existing cards."""
        state = AppState()

        card1 = WebCard(
            title="First Card",
            url=HttpUrl("https://example.com"),
            large_summary="First summary content.",
        )

        card2 = WebCard(
            title="Second Card",
            url=HttpUrl("https://example.com"),  # Same URL
            large_summary="Second summary content.",
        )

        state.add_web_card(card1)
        state.add_web_card(card2)

        # Should only have one card (the second one)
        assert len(state.active_cards) == 1
        assert state.active_cards[0].title == "Second Card"

    def test_clear_results(self):
        """Test clearing all results."""
        state = AppState()

        # Add some data
        state.current_search_query = "test query"
        state.add_search_results(
            [SearchResult(title="Test", url=HttpUrl("https://example.com"))]
        )
        state.add_web_card(
            WebCard(
                title="Test",
                url=HttpUrl("https://example.com"),
                large_summary="Test summary content.",
            )
        )
        state.set_error("Test error")

        # Clear everything
        state.clear_results()

        assert state.current_search_query == ""
        assert len(state.search_results) == 0
        assert len(state.active_cards) == 0
        assert state.last_error == ""

    def test_session_duration(self):
        """Test session duration calculation."""
        state = AppState()
        duration = state.get_session_duration()

        # Should be in format HH:MM:SS
        assert isinstance(duration, str)
        assert len(duration.split(":")) == 3
