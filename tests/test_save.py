"""
Unit tests for save functionality.
"""

import pytest
import sys
import tempfile
import os
import json
import csv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.save import (
    sanitize_filename, 
    generate_filename_from_url, 
    write_json_per_article,
    get_saved_articles_count,
    ensure_output_dir
)


class TestSaveUtilities:
    """Test cases for save utility functions."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        # Normal title
        result = sanitize_filename("Breaking News: Tech Giant Announces New Product")
        expected = "breaking-news-tech-giant-announces-new-product"
        assert result == expected
        
        # Title with special characters
        result = sanitize_filename("COVID-19: What's Next? (Updated 2024)")
        expected = "covid-19-whats-next-updated-2024"
        assert result == expected
        
        # Empty title
        result = sanitize_filename("")
        assert result == "untitled"
        
        # None title
        result = sanitize_filename(None)
        assert result == "untitled"
    
    def test_sanitize_filename_length_limit(self):
        """Test filename length limiting."""
        long_title = "This is a very long article title that exceeds the maximum length limit and should be truncated properly"
        result = sanitize_filename(long_title, max_length=50)
        
        assert len(result) <= 50
        assert not result.endswith('-')  # Should not end with hyphen
        assert result.startswith("this-is-a-very-long")
    
    def test_sanitize_filename_special_characters(self):
        """Test handling of various special characters."""
        test_cases = [
            ("Article with @#$%^&*() symbols", "article-with-symbols"),
            ("Title/with\\slashes", "titlewithslashes"),
            ("Multiple   spaces    here", "multiple-spaces-here"),
            ("---Multiple---Hyphens---", "multiple-hyphens"),
            ("Title.with.dots", "titlewith-dots"),
        ]
        
        for input_title, expected in test_cases:
            result = sanitize_filename(input_title)
            assert result == expected, f"Input: {input_title}, Expected: {expected}, Got: {result}"
    
    def test_generate_filename_from_url(self):
        """Test filename generation from URL."""
        url = "https://example.com/news/article/123"
        result = generate_filename_from_url(url)
        
        # Should start with 'article-' and have 8-char hash
        assert result.startswith("article-")
        assert len(result) == len("article-") + 8
        
        # Same URL should generate same filename
        result2 = generate_filename_from_url(url)
        assert result == result2
        
        # Different URL should generate different filename
        different_url = "https://example.com/news/article/456"
        result3 = generate_filename_from_url(different_url)
        assert result != result3
    
    def test_ensure_output_dir(self):
        """Test output directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output", "nested")
            
            # Directory should not exist initially
            assert not os.path.exists(output_path)
            
            # Should create directory
            ensure_output_dir(output_path)
            assert os.path.exists(output_path)
            assert os.path.isdir(output_path)
            
            # Should not raise error if directory already exists
            ensure_output_dir(output_path)  # Second call
            assert os.path.exists(output_path)
    
    def test_write_json_per_article(self):
        """Test writing article data to JSON and CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            article_data = {
                "title": "Test Article Title",
                "url": "https://example.com/test",
                "author": "Test Author",
                "published_date": "2024-01-01",
                "content": "This is test content for the article.",
                "summary": "Test summary"
            }
            
            # Write article
            success = write_json_per_article(article_data, temp_dir)
            assert success
            
            # Check JSON file was created
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
            assert len(json_files) == 1
            
            json_file = json_files[0]
            assert json_file == "test-article-title.json"
            
            # Verify JSON content
            json_path = os.path.join(temp_dir, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                assert saved_data == article_data
            
            # Check CSV file was created
            csv_path = os.path.join(temp_dir, 'all_articles.csv')
            assert os.path.exists(csv_path)
            
            # Verify CSV content
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['title'] == article_data['title']
                assert rows[0]['url'] == article_data['url']
    
    def test_write_multiple_articles(self):
        """Test writing multiple articles and CSV accumulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            articles = [
                {
                    "title": "First Article",
                    "url": "https://example.com/first",
                    "author": "Author 1",
                    "published_date": "2024-01-01",
                    "content": "Content 1",
                    "summary": "Summary 1"
                },
                {
                    "title": "Second Article",
                    "url": "https://example.com/second",
                    "author": "Author 2",
                    "published_date": "2024-01-02",
                    "content": "Content 2",
                    "summary": "Summary 2"
                }
            ]
            
            # Write both articles
            for article in articles:
                success = write_json_per_article(article, temp_dir)
                assert success
            
            # Check JSON files
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
            assert len(json_files) == 2
            
            # Check CSV accumulation
            csv_path = os.path.join(temp_dir, 'all_articles.csv')
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['title'] == "First Article"
                assert rows[1]['title'] == "Second Article"
    
    def test_write_article_without_title(self):
        """Test writing article without title (should use URL hash)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            article_data = {
                "title": "",  # Empty title
                "url": "https://example.com/no-title",
                "author": "Test Author",
                "published_date": "2024-01-01",
                "content": "Content without title",
                "summary": "Summary"
            }
            
            success = write_json_per_article(article_data, temp_dir)
            assert success
            
            # Should use URL hash for filename
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
            assert len(json_files) == 1
            assert json_files[0].startswith("article-")
    
    def test_duplicate_filename_handling(self):
        """Test handling of duplicate filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create two articles with same title
            article1 = {
                "title": "Duplicate Title",
                "url": "https://example.com/first",
                "content": "Content 1"
            }
            
            article2 = {
                "title": "Duplicate Title",
                "url": "https://example.com/second", 
                "content": "Content 2"
            }
            
            # Write both articles
            success1 = write_json_per_article(article1, temp_dir)
            success2 = write_json_per_article(article2, temp_dir)
            
            assert success1 and success2
            
            # Should have two different filenames
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
            assert len(json_files) == 2
            
            # One should be original, one should have counter
            filenames = set(json_files)
            assert "duplicate-title.json" in filenames
            assert "duplicate-title-1.json" in filenames
    
    def test_get_saved_articles_count(self):
        """Test counting saved articles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initially should be 0
            count = get_saved_articles_count(temp_dir)
            assert count == 0
            
            # Add some JSON files
            for i in range(3):
                json_path = os.path.join(temp_dir, f"article-{i}.json")
                with open(json_path, 'w') as f:
                    json.dump({"title": f"Article {i}"}, f)
            
            # Should count JSON files
            count = get_saved_articles_count(temp_dir)
            assert count == 3
            
            # Add non-JSON file (should not be counted)
            txt_path = os.path.join(temp_dir, "readme.txt")
            with open(txt_path, 'w') as f:
                f.write("This is not JSON")
            
            # Count should remain the same
            count = get_saved_articles_count(temp_dir)
            assert count == 3
            
        # Non-existent directory should return 0
        count = get_saved_articles_count("/non/existent/path")
        assert count == 0


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
