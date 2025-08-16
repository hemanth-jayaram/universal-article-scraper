"""
Unit tests for link filtering functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.link_filters import suggest_article_links, _looks_like_article, _clean_url


class TestLinkFilters:
    """Test cases for link filtering functions."""
    
    def test_suggest_article_links_basic(self):
        """Test basic article link filtering."""
        homepage_url = "https://example.com"
        links = [
            "/news/article-1",
            "/blog/post-1", 
            "/category/tech",
            "/contact",
            "/article/breaking-news",
            "https://otherdomain.com/news",  # Different domain
            "/2024/01/15/story"
        ]
        
        result = suggest_article_links(homepage_url, links)
        
        # Should filter to same-domain article-like links
        assert len(result) > 0
        assert all("example.com" in url for url in result)
        assert any("news/article-1" in url for url in result)
        assert any("blog/post-1" in url for url in result)
        assert any("article/breaking-news" in url for url in result)
        assert not any("contact" in url for url in result)
        assert not any("otherdomain.com" in url for url in result)
    
    def test_suggest_article_links_deduplication(self):
        """Test that duplicate links are removed."""
        homepage_url = "https://example.com"
        links = [
            "/news/article-1",
            "/news/article-1",  # Duplicate
            "/news/article-1?utm_source=twitter",  # Same but with tracking
            "/blog/post-1"
        ]
        
        result = suggest_article_links(homepage_url, links)
        
        # Should contain unique URLs only
        assert len(result) == 2  # article-1 and post-1
        assert len(set(result)) == len(result)  # All unique
    
    def test_clean_url(self):
        """Test URL cleaning functionality."""
        # Test tracking parameter removal
        url_with_tracking = "https://example.com/article?utm_source=facebook&utm_campaign=test&id=123"
        cleaned = _clean_url(url_with_tracking)
        assert "utm_source" not in cleaned
        assert "utm_campaign" not in cleaned
        assert "id=123" in cleaned  # Non-tracking param should remain
        
        # Test fragment removal
        url_with_fragment = "https://example.com/article#section1"
        cleaned = _clean_url(url_with_fragment)
        assert "#section1" not in cleaned
        
        # Test clean URL remains unchanged
        clean_url = "https://example.com/article"
        cleaned = _clean_url(clean_url)
        assert cleaned == clean_url
    
    def test_looks_like_article_positive_cases(self):
        """Test URLs that should be identified as articles."""
        article_urls = [
            "https://example.com/news/breaking-story",
            "https://example.com/article/tech-review",
            "https://example.com/blog/my-experience",
            "https://example.com/2024/01/15/daily-update",
            "https://example.com/stories/amazing-discovery",
            "https://example.com/reviews/product-review",
            "https://example.com/opinion/editorial-piece",
            "https://example.com/long-article-title-with-many-words"
        ]
        
        for url in article_urls:
            assert _looks_like_article(url), f"Should identify as article: {url}"
    
    def test_looks_like_article_negative_cases(self):
        """Test URLs that should NOT be identified as articles."""
        non_article_urls = [
            "https://example.com/contact",
            "https://example.com/about",
            "https://example.com/category/tech",
            "https://example.com/tag/politics",
            "https://example.com/live",
            "https://example.com/video/watch",
            "https://example.com/search?q=test",
            "https://example.com/privacy",
            "https://example.com/sitemap.xml",
            "https://example.com/feed.rss",
            "https://example.com/api/endpoint"
        ]
        
        for url in non_article_urls:
            assert not _looks_like_article(url), f"Should NOT identify as article: {url}"
    
    def test_looks_like_article_edge_cases(self):
        """Test edge cases for article detection."""
        # URLs with date patterns
        date_urls = [
            "https://example.com/2024/politics",
            "https://example.com/news/2023/12/story",
            "https://example.com/2024-01-15-breaking"
        ]
        
        for url in date_urls:
            assert _looks_like_article(url), f"Date pattern should be article: {url}"
        
        # Long slug patterns
        slug_urls = [
            "https://example.com/this-is-a-very-long-article-title",
            "https://example.com/multiple-word-slug-pattern"
        ]
        
        for url in slug_urls:
            assert _looks_like_article(url), f"Long slug should be article: {url}"
    
    def test_cross_domain_filtering(self):
        """Test that cross-domain links are filtered out."""
        homepage_url = "https://example.com"
        links = [
            "https://example.com/news/story1",  # Same domain
            "https://other.com/news/story2",    # Different domain
            "https://subdomain.example.com/news/story3",  # Different subdomain
            "/relative/path"  # Relative (should become same domain)
        ]
        
        result = suggest_article_links(homepage_url, links)
        
        # Should only contain same-domain links
        same_domain_count = sum(1 for url in result if "example.com" in url and "subdomain" not in url)
        assert same_domain_count >= 1  # At least the relative path and same domain
        assert not any("other.com" in url for url in result)
        assert not any("subdomain.example.com" in url for url in result)


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
