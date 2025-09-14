"""Unit tests for SLBrowser web module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from slbrowser import NetworkError
from slbrowser.web import WebScraper


class TestWebScraper:
    """Test cases for WebScraper class."""

    def test_web_scraper_initialization(self):
        """Test WebScraper initialization."""
        scraper = WebScraper()
        assert scraper.timeout == 30.0
        assert scraper.max_retries == 3
        assert scraper.user_agent is not None

    def test_web_scraper_custom_config(self):
        """Test WebScraper with custom configuration."""
        scraper = WebScraper(timeout=60.0, max_retries=5, user_agent="Custom Agent")
        assert scraper.timeout == 60.0
        assert scraper.max_retries == 5
        assert scraper.user_agent == "Custom Agent"

    @pytest.mark.asyncio
    async def test_fetch_content_success(self, sample_html_content):
        """Test successful content fetching."""
        scraper = WebScraper()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = sample_html_content
            mock_response.headers = {"content-type": "text/html"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            content = await scraper.fetch_content("https://example.com")

            assert content is not None
            assert "Test Article Title" in content
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_fetch_content_404_error(self):
        """Test handling of 404 errors."""
        scraper = WebScraper()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=MagicMock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            with pytest.raises(NetworkError):
                await scraper.fetch_content("https://example.com/nonexistent")

    @pytest.mark.asyncio
    async def test_fetch_content_timeout(self):
        """Test handling of timeout errors."""
        scraper = WebScraper()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.TimeoutException("Timeout")
            )

            with pytest.raises(NetworkError):
                await scraper.fetch_content("https://slow-site.com")

    @pytest.mark.asyncio
    async def test_fetch_content_connection_error(self):
        """Test handling of connection errors."""
        scraper = WebScraper()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.ConnectError("Connection failed")
            )

            with pytest.raises(NetworkError):
                await scraper.fetch_content("https://unreachable.com")

    def test_extract_text_from_html(self, sample_html_content):
        """Test HTML text extraction."""
        scraper = WebScraper()
        text = scraper.extract_text(sample_html_content)

        assert "Test Article Title" in text
        assert "first paragraph" in text
        assert "second paragraph" in text
        assert "First list item" in text
        # HTML tags should be removed
        assert "<h1>" not in text
        assert "<p>" not in text

    def test_extract_text_from_plain_text(self):
        """Test extraction from plain text (no HTML)."""
        scraper = WebScraper()
        plain_text = "This is just plain text without any HTML tags."

        result = scraper.extract_text(plain_text)
        assert result == plain_text

    def test_extract_text_empty_content(self):
        """Test extraction from empty content."""
        scraper = WebScraper()

        assert scraper.extract_text("") == ""
        assert scraper.extract_text(None) == ""

    def test_extract_text_malformed_html(self):
        """Test extraction from malformed HTML."""
        scraper = WebScraper()
        malformed_html = "<div><p>Unclosed paragraph<span>Unclosed span</div>"

        # Should still extract text even with malformed HTML
        result = scraper.extract_text(malformed_html)
        assert "Unclosed paragraph" in result
        assert "Unclosed span" in result

    def test_extract_links_from_html(self, sample_html_content):
        """Test link extraction from HTML."""
        scraper = WebScraper()
        links = scraper.extract_links(sample_html_content, "https://example.com")

        assert len(links) > 0
        assert any("https://example.com" in link for link in links)

    def test_extract_links_relative_urls(self):
        """Test extraction and resolution of relative URLs."""
        scraper = WebScraper()
        html_with_relative = """
        <html>
            <body>
                <a href="/relative/path">Relative link</a>
                <a href="../parent/path">Parent relative</a>
                <a href="same-level.html">Same level</a>
            </body>
        </html>
        """

        links = scraper.extract_links(
            html_with_relative, "https://example.com/current/page"
        )

        # Should resolve relative URLs to absolute
        absolute_links = [link for link in links if link.startswith("http")]
        assert len(absolute_links) > 0

    def test_extract_dates_from_html(self, sample_html_content):
        """Test date extraction from HTML."""
        scraper = WebScraper()
        dates = scraper.extract_dates(sample_html_content)

        assert len(dates) > 0
        assert "2024-01-15" in dates

    def test_extract_dates_various_formats(self):
        """Test extraction of dates in various formats."""
        scraper = WebScraper()
        html_with_dates = """
        <html>
            <body>
                <time datetime="2024-01-15">January 15, 2024</time>
                <span>Published on 2024/01/15</span>
                <div>Date: 15-01-2024</div>
                <p>Updated: Jan 15, 2024</p>
            </body>
        </html>
        """

        dates = scraper.extract_dates(html_with_dates)

        # Should find multiple date formats
        assert len(dates) > 0

    @pytest.mark.asyncio
    async def test_scrape_url_full_workflow(self, sample_html_content):
        """Test complete URL scraping workflow."""
        scraper = WebScraper()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = sample_html_content
            mock_response.headers = {"content-type": "text/html"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await scraper.scrape_url("https://example.com/test")

            assert result is not None
            assert "content" in result
            assert "links" in result
            assert "dates" in result
            assert len(result["content"]) > 0

    def test_clean_text(self):
        """Test text cleaning functionality."""
        scraper = WebScraper()

        messy_text = (
            "  This   has    too   much    whitespace   \n\n\n  and newlines  \t\t  "
        )
        cleaned = scraper.clean_text(messy_text)

        assert cleaned == "This has too much whitespace and newlines"

    def test_clean_text_preserve_structure(self):
        """Test that text cleaning preserves some structure."""
        scraper = WebScraper()

        structured_text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        cleaned = scraper.clean_text(structured_text)

        # Should preserve paragraph breaks
        assert "\n\n" in cleaned or len(cleaned.split(".")) == 3

    def test_is_valid_url(self):
        """Test URL validation."""
        scraper = WebScraper()

        assert scraper.is_valid_url("https://example.com")
        assert scraper.is_valid_url("http://example.com")
        assert scraper.is_valid_url("https://example.com/path/to/page")

        assert not scraper.is_valid_url("not-a-url")
        assert not scraper.is_valid_url("ftp://example.com")  # Only HTTP(S) allowed
        assert not scraper.is_valid_url("")
        assert not scraper.is_valid_url(None)
