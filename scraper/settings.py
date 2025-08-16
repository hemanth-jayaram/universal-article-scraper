"""
Scrapy settings for homepage article scraper.
Optimized for speed and single-page discovery.
"""

import os
from typing import Dict, Any


def get_scrapy_settings() -> Dict[str, Any]:
    """Get optimized Scrapy settings for fast article discovery."""
    
    return {
        # Bot identification
        'BOT_NAME': 'homepage-article-scraper',
        'USER_AGENT': 'Mozilla/5.0 (compatible; HomepageArticleBot/1.0; +https://github.com/scraper)',
        
        # Crawling behavior
        'ROBOTSTXT_OBEY': False,  # Explicit requirement to ignore robots.txt
        'DEPTH_LIMIT': 1,  # Only homepage + discovered articles
        
        # Performance settings (overridable via env vars)
        'CONCURRENT_REQUESTS': int(os.getenv('CONCURRENT_REQUESTS', 32)),
        'CONCURRENT_REQUESTS_PER_DOMAIN': int(os.getenv('CONCURRENT_REQUESTS_PER_DOMAIN', 16)),
        'DOWNLOAD_DELAY': float(os.getenv('DOWNLOAD_DELAY', 0)),
        'RETRY_TIMES': int(os.getenv('RETRY_TIMES', 1)),
        
        # DNS and caching
        'DNSCACHE_ENABLED': True,
        'DNSCACHE_SIZE': 10000,
        
        # Request processing
        'DOWNLOAD_TIMEOUT': 30,
        'REDIRECT_MAX_TIMES': 3,
        
        # Disable unnecessary middleware for speed
        'TELNETCONSOLE_ENABLED': False,
        'COOKIES_ENABLED': False,
        'COMPRESSION_ENABLED': True,
        
        # AutoThrottle settings (optional rate limiting)
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0,
        'AUTOTHROTTLE_MAX_DELAY': 1,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 8.0,
        'AUTOTHROTTLE_DEBUG': False,
        
        # Logging
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        
        # Memory optimization
        'MEMDEBUG_ENABLED': False,
        'MEMUSAGE_ENABLED': True,
        'MEMUSAGE_LIMIT_MB': 2048,
        'MEMUSAGE_WARNING_MB': 1024,
        
        # Item pipelines
        'ITEM_PIPELINES': {},
        
        # Spider modules
        'SPIDER_MODULES': ['scraper.spiders'],
        'NEWSPIDER_MODULE': 'scraper.spiders',
    }


# Export settings for direct use
SCRAPY_SETTINGS = get_scrapy_settings()
