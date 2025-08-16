"""
Generic homepage spider that discovers and scrapes article links.
"""

import os
import time
from urllib.parse import urlparse
from typing import Generator, Any, Dict, Optional

import scrapy
from scrapy import Request
from scrapy.http import Response

from scraper.link_filters import suggest_article_links
from scraper.extractors import extract_article
from scraper.summarizer import summarize
from scraper.save import write_json_per_article, ensure_output_dir

import logging

logger = logging.getLogger(__name__)


class HomepageSpider(scrapy.Spider):
    """
    Spider that accepts a start_url and scrapes articles from the homepage.
    
    Usage:
        scrapy crawl homepage -a start_url="https://example.com" -a out_dir="output"
    """
    
    name = 'homepage'
    
    def __init__(self, start_url: str = None, out_dir: str = 'output', *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not start_url:
            raise ValueError("start_url is required")
        
        self.start_urls = [start_url]
        self.out_dir = out_dir
        self.start_time = time.time()
        self.articles_found = 0
        self.articles_processed = 0
        self.articles_saved = 0
        
        # Extract domain for allowed_domains
        parsed_url = urlparse(start_url)
        self.allowed_domains = [parsed_url.netloc]
        
        # Get max articles limit
        self.max_articles = int(os.getenv('MAX_ARTICLES', 40))
        
        # Ensure output directory exists
        ensure_output_dir(self.out_dir)
        
        logger.info(f"Starting scrape of {start_url}")
        logger.info(f"Output directory: {self.out_dir}")
        logger.info(f"Max articles: {self.max_articles}")
    
    def parse(self, response: Response) -> Generator[Request, None, None]:
        """
        Parse the homepage to discover article links.
        
        Args:
            response: The homepage response
            
        Yields:
            Request objects for discovered article URLs
        """
        logger.info(f"Parsing homepage: {response.url}")
        
        # Extract all links from the page
        links = response.css('a::attr(href)').getall()
        logger.info(f"Found {len(links)} total links on homepage")
        
        # Filter to potential article links
        article_links = suggest_article_links(response.url, links)
        self.articles_found = len(article_links)
        
        # Limit articles if specified
        if self.max_articles > 0:
            article_links = article_links[:self.max_articles]
            logger.info(f"Limited to {len(article_links)} articles (max: {self.max_articles})")
        
        logger.info(f"Processing {len(article_links)} potential articles")
        
        # Generate requests for each article
        for url in article_links:
            yield Request(
                url=url,
                callback=self.parse_article,
                errback=self.handle_error,
                meta={'start_url': response.url}
            )
    
    def parse_article(self, response: Response) -> None:
        """
        Parse an individual article page.
        
        Args:
            response: The article page response
        """
        self.articles_processed += 1
        logger.info(f"Processing article {self.articles_processed}/{self.articles_found}: {response.url}")
        
        try:
            # Extract article content
            article_data = extract_article(response)
            
            if not article_data or not article_data.get('content'):
                logger.warning(f"No content extracted from {response.url}")
                return
            
            # Generate summary if content is substantial
            content = article_data['content']
            if len(content) > 300 and os.getenv('SUMMARY_ENABLED', 'true').lower() == 'true':
                try:
                    summary = summarize(content)
                    article_data['summary'] = summary
                except Exception as e:
                    logger.warning(f"Summarization failed for {response.url}: {e}")
                    article_data['summary'] = self._fallback_summary(content)
            else:
                article_data['summary'] = content if len(content) <= 300 else "N/A"
            
            # Ensure URL is set
            article_data['url'] = response.url
            
            # Save the article
            success = write_json_per_article(article_data, self.out_dir)
            if success:
                self.articles_saved += 1
                logger.info(f"Saved article: {article_data.get('title', 'Untitled')}")
            else:
                logger.error(f"Failed to save article from {response.url}")
                
        except Exception as e:
            logger.error(f"Error processing article {response.url}: {e}")
    
    def handle_error(self, failure) -> None:
        """Handle request failures."""
        logger.error(f"Request failed: {failure.request.url} - {failure.value}")
    
    def closed(self, reason: str) -> None:
        """Called when the spider is closed."""
        elapsed_time = time.time() - self.start_time
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Homepage: {self.start_urls[0]}")
        logger.info(f"Total links found: {self.articles_found}")
        logger.info(f"Articles processed: {self.articles_processed}")
        logger.info(f"Articles saved: {self.articles_saved}")
        logger.info(f"Output directory: {self.out_dir}")
        logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        logger.info(f"Reason: {reason}")
        logger.info("=" * 60)
    
    def _fallback_summary(self, content: str, max_sentences: int = 3) -> str:
        """
        Create a fallback summary by taking the first few sentences.
        
        Args:
            content: The full content text
            max_sentences: Maximum number of sentences to include
            
        Returns:
            A simple summary based on first sentences
        """
        sentences = content.split('. ')
        if len(sentences) <= max_sentences:
            return content
        
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        # Ensure it ends with a period
        if not summary.endswith('.'):
            summary += '.'
            
        return summary
