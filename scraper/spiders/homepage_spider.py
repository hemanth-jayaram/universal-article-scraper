"""
Generic homepage spider that discovers and scrapes article links.
"""

import os
import time
from urllib.parse import urlparse
from typing import Generator, Any, Dict, Optional, List

import scrapy
from scrapy import Request
from scrapy.http import Response

from scraper.link_filters import suggest_article_links
from scraper.extractors import extract_article
from scraper.summarizer import summarize
from scraper.save import write_json_per_article, ensure_output_dir, finalize_s3_csv_upload, create_summary_report
try:
    from scraper.s3_upload import get_s3_uploader, is_s3_configured
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file if available
try:
    import sys
    import os
    # Add project root to path for importing load_env
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from load_env import load_env_file
    load_env_file()
    logger.debug("Environment variables loaded from .env file")
except ImportError:
    logger.debug("load_env module not available, using system environment variables only")
except Exception as e:
    logger.debug(f"Could not load .env file: {e}")


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
        
        # NEW: Store articles in memory for filtering before saving
        self.scraped_articles = []
        self.filtered_articles = []
        
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
            
            # NEW: Store article in memory instead of saving immediately
            self.scraped_articles.append(article_data)
            logger.info(f"Scraped article: {article_data.get('title', 'Untitled')}")
                
        except Exception as e:
            logger.error(f"Error processing article {response.url}: {e}")
    
    def handle_error(self, failure) -> None:
        """Handle request failures."""
        logger.error(f"Request failed: {failure.request.url} - {failure.value}")
    
    def closed(self, reason: str) -> None:
        """Called when the spider is closed."""
        elapsed_time = time.time() - self.start_time
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE - STARTING FILTERING")
        logger.info("=" * 60)
        logger.info(f"Homepage: {self.start_urls[0]}")
        logger.info(f"Total links found: {self.articles_found}")
        logger.info(f"Articles processed: {self.articles_processed}")
        logger.info(f"Articles scraped: {len(self.scraped_articles)}")
        logger.info(f"Output directory: {self.out_dir}")
        logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        logger.info(f"Reason: {reason}")
        
        # NEW: Filter articles before saving
        if self.scraped_articles:
            logger.info("🔍 Starting article filtering...")
            self.filter_articles()
            logger.info(f"✅ Filtering complete: {len(self.filtered_articles)} articles passed filter")
            
            # Save only filtered articles
            logger.info("💾 Saving filtered articles...")
            self.save_filtered_articles()
            logger.info(f"💾 Saving complete: {self.articles_saved} articles saved")
        else:
            logger.warning("⚠️ No articles were scraped successfully")
        
        # Create summary report
        try:
            use_s3 = S3_AVAILABLE and is_s3_configured()
            summary_location = create_summary_report(
                output_dir=self.out_dir,
                homepage_url=self.start_urls[0],
                total_found=self.articles_found,
                processed=self.articles_processed,
                saved=self.articles_saved,
                elapsed_time=elapsed_time,
                use_s3=use_s3
            )
            if summary_location:
                storage_type = "S3" if use_s3 else "local file"
                logger.info(f"📋 Summary report created ({storage_type}): {summary_location}")
        except Exception as e:
            logger.error(f"Failed to create summary report: {e}")
        
        logger.info("=" * 60)
        logger.info("FINAL RESULTS")
        logger.info("=" * 60)
        logger.info(f"Articles scraped: {len(self.scraped_articles)}")
        logger.info(f"Articles filtered: {len(self.filtered_articles)}")
        logger.info(f"Articles saved: {self.articles_saved}")
        logger.info(f"Storage type: {'S3 bucket' if S3_AVAILABLE and is_s3_configured() else 'Local filesystem'}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info("=" * 60)
    
    def filter_articles(self) -> None:
        """Filter scraped articles using the same logic as filter_articles.py."""
        # First try to import the filtering function
        is_actual_article = None
        
        # Try multiple import paths to ensure compatibility
        import_attempts = [
            # Path 1: Direct import (for local execution)
            lambda: __import__('filter_articles', fromlist=['is_actual_article']).is_actual_article,
            # Path 2: From project root (for remote execution)
            lambda: self._import_from_project_root(),
            # Path 3: From current working directory
            lambda: self._import_from_cwd(),
        ]
        
        for attempt in import_attempts:
            try:
                is_actual_article = attempt()
                if is_actual_article:
                    logger.info("✅ Successfully imported filtering function")
                    break
            except (ImportError, AttributeError, Exception) as e:
                logger.debug(f"Import attempt failed: {e}")
                continue
        
        if not is_actual_article:
            logger.error("❌ Failed to import filter_articles module. Falling back to saving all articles.")
            # If filtering fails completely, include all articles to be safe
            self.filtered_articles = self.scraped_articles.copy()
            return
        
        logger.info(f"🔍 Filtering {len(self.scraped_articles)} scraped articles...")
        
        for article_data in self.scraped_articles:
            try:
                # Use the same filtering logic from filter_articles.py
                is_article, reason = is_actual_article(article_data)
                
                if is_article:
                    self.filtered_articles.append(article_data)
                    logger.debug(f"✅ Article passed filter: {article_data.get('title', 'Untitled')}")
                else:
                    logger.debug(f"❌ Article filtered out: {article_data.get('title', 'Untitled')} - {reason}")
                    
            except Exception as e:
                logger.error(f"Error filtering article {article_data.get('title', 'Untitled')}: {e}")
                # If filtering fails, include the article to be safe
                self.filtered_articles.append(article_data)
        
        logger.info(f"🔍 Filtering complete: {len(self.filtered_articles)}/{len(self.scraped_articles)} articles passed filter")
    
    def _import_from_project_root(self):
        """Try to import filter_articles from project root."""
        import sys
        import os
        
        # Get the project root (3 levels up from this file)
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from filter_articles import is_actual_article
        return is_actual_article
    
    def _import_from_cwd(self):
        """Try to import filter_articles from current working directory."""
        import sys
        import os
        
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        
        from filter_articles import is_actual_article
        return is_actual_article
    
    def save_filtered_articles(self) -> None:
        """Save only the filtered articles."""
        logger.info(f"💾 Saving {len(self.filtered_articles)} filtered articles...")
        
        # Always use S3 upload - force S3 usage
        use_s3 = True
        if not S3_AVAILABLE:
            logger.error("❌ S3 module not available")
            raise Exception("S3 module not available")
        
        if not is_s3_configured():
            logger.error("❌ S3 is not configured but required for this scraper")
            logger.error("   Please configure S3 settings in .env file")
            raise Exception("S3 configuration required but not found")
        
        logger.info("🚀 Using S3 upload for articles")
        
        for article_data in self.filtered_articles:
            try:
                success = write_json_per_article(article_data, self.out_dir, use_s3=use_s3)
                if success:
                    self.articles_saved += 1
                    storage_type = "S3" if use_s3 else "locally"
                    logger.debug(f"💾 Saved {storage_type}: {article_data.get('title', 'Untitled')}")
                else:
                    logger.error(f"❌ Failed to save: {article_data.get('title', 'Untitled')}")
            except Exception as e:
                logger.error(f"Error saving article {article_data.get('title', 'Untitled')}: {e}")
        
        # Finalize S3 CSV upload if using S3
        if use_s3 and S3_AVAILABLE:
            try:
                uploader = get_s3_uploader(prefix=self.out_dir)
                if uploader:
                    csv_success = finalize_s3_csv_upload(uploader)
                    if csv_success:
                        logger.info("📊 CSV file uploaded to S3 successfully")
                    else:
                        logger.error("❌ Failed to upload CSV to S3")
                else:
                    logger.error("❌ S3 uploader not available for CSV upload")
            except Exception as e:
                logger.error(f"Error uploading CSV to S3: {e}")
        
        storage_location = f"S3 bucket ({self.out_dir})" if use_s3 else f"local directory ({self.out_dir})"
        logger.info(f"💾 Saving complete: {self.articles_saved} articles saved to {storage_location}")
    
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
