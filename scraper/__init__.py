"""
Homepage Article Scraper

A high-performance web scraper for extracting articles from news websites and blogs
with AI-powered summarization using local BERT/BART models.
"""

__version__ = "1.0.0"
__author__ = "Homepage Article Scraper Team"
__email__ = "contact@example.com"
__description__ = "High-performance web scraper with AI summarization"
__url__ = "https://github.com/yourusername/homepage-article-scraper"
__license__ = "MIT"

# Core imports
from .extractors import extract_article
from .link_filters import suggest_article_links
from .summarizer import summarize, get_summarizer
from .save import write_json_per_article, create_summary_report

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "__url__",
    "__license__",
    "extract_article",
    "suggest_article_links",
    "summarize",
    "get_summarizer",
    "write_json_per_article",
    "create_summary_report",
]
