#!/usr/bin/env python3
"""
CLI entry point for the Homepage Article Scraper.

Usage:
    python run.py "https://www.bbc.com/news" --out output
"""

import argparse
import os
import sys
import time
import logging
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging

from scraper.settings import get_scrapy_settings
from scraper.spiders.homepage_spider import HomepageSpider
from scraper.save import create_summary_report, get_saved_articles_count


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure Scrapy logging
    configure_logging({
        'LOG_LEVEL': 'DEBUG' if verbose else 'INFO',
        'LOG_FORMAT': '%(levelname)s: %(message)s'
    })
    
    # Configure our own logging
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
        force=True
    )


def validate_url(url: str) -> str:
    """
    Validate and normalize the input URL.
    
    Args:
        url: Input URL string
        
    Returns:
        Normalized URL
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Add https:// if no scheme provided
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Basic validation
    if not any(url.startswith(scheme) for scheme in ['http://', 'https://']):
        raise ValueError("Invalid URL format")
    
    return url


def run_scraper(homepage_url: str, output_dir: str, verbose: bool = False) -> tuple:
    """
    Run the scraper programmatically.
    
    Args:
        homepage_url: The homepage URL to scrape
        output_dir: Output directory for results
        verbose: Enable verbose logging
        
    Returns:
        Tuple of (success, statistics_dict)
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate inputs
        homepage_url = validate_url(homepage_url)
        
        logger.info("=" * 60)
        logger.info("HOMEPAGE ARTICLE SCRAPER")
        logger.info("=" * 60)
        logger.info(f"Target URL: {homepage_url}")
        logger.info(f"Output directory: {output_dir}")
        logger.info("")
        
        start_time = time.time()
        
        # Get Scrapy settings
        settings = get_scrapy_settings()
        
        # Create and configure the crawler process
        process = CrawlerProcess(settings)
        
        # Add the spider to the process
        process.crawl(
            HomepageSpider,
            start_url=homepage_url,
            out_dir=output_dir
        )
        
        # Start the crawling process
        process.start()  # This will block until crawling is complete
        
        elapsed_time = time.time() - start_time
        
        # Get final statistics
        saved_count = get_saved_articles_count(output_dir)
        
        # Create summary report
        create_summary_report(
            output_dir=output_dir,
            homepage_url=homepage_url,
            total_found=0,  # Will be updated by spider
            processed=0,    # Will be updated by spider
            saved=saved_count,
            elapsed_time=elapsed_time
        )
        
        logger.info("")
        logger.info("SCRAPING COMPLETED SUCCESSFULLY")
        logger.info(f"Articles saved: {saved_count}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info(f"Results available in: {output_dir}")
        
        return True, {
            'saved_count': saved_count,
            'elapsed_time': elapsed_time,
            'output_dir': output_dir
        }
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return False, {'error': str(e)}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Homepage Article Scraper - Extract and summarize articles from news/blog homepages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py "https://www.bbc.com/news"
  python run.py "https://techcrunch.com" --out articles
  python run.py "https://www.reuters.com" --out output --verbose
  
Environment Variables:
  CONCURRENT_REQUESTS         Number of concurrent requests (default: 32)
  CONCURRENT_REQUESTS_PER_DOMAIN  Requests per domain (default: 16)
  DOWNLOAD_DELAY             Delay between requests in seconds (default: 0)
  MAX_ARTICLES               Maximum articles to process (default: 40)
  SUMMARY_ENABLED            Enable summarization (default: true)
        """
    )
    
    parser.add_argument(
        'url',
        help='Homepage URL to scrape (e.g., "https://www.bbc.com/news")'
    )
    
    parser.add_argument(
        '--out',
        default='output',
        help='Output directory for saved articles (default: output)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Homepage Article Scraper 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Run the scraper
    success, stats = run_scraper(args.url, args.out, args.verbose)
    
    if success:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📁 Results saved to: {stats['output_dir']}")
        print(f"📄 Articles saved: {stats['saved_count']}")
        print(f"⏱️  Time taken: {stats['elapsed_time']:.1f} seconds")
        sys.exit(0)
    else:
        print(f"\n❌ Scraping failed: {stats.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
