"""
Link filtering heuristics to identify article URLs from homepage links.
"""

import re
from urllib.parse import urljoin, urlparse
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


def suggest_article_links(homepage_url: str, links: List[str]) -> List[str]:
    """
    Filter homepage links to identify potential article URLs.
    
    Args:
        homepage_url: The original homepage URL for domain filtering
        links: List of extracted links from the homepage
    
    Returns:
        List of filtered, deduplicated article URLs
    """
    parsed_homepage = urlparse(homepage_url)
    base_domain = parsed_homepage.netloc.lower()
    
    article_links: Set[str] = set()
    
    for link in links:
        # Convert to absolute URL
        absolute_url = urljoin(homepage_url, link)
        parsed_url = urlparse(absolute_url)
        
        # Only keep same-site links
        if parsed_url.netloc.lower() != base_domain:
            continue
            
        # Clean URL (remove fragments, tracking params)
        clean_url = _clean_url(absolute_url)
        if not clean_url:
            continue
            
        # Apply article detection heuristics
        if _looks_like_article(clean_url):
            article_links.add(clean_url)
    
    result = list(article_links)
    logger.info(f"Filtered {len(links)} links to {len(result)} potential articles")
    return result


def _clean_url(url: str) -> str:
    """Clean URL by removing fragments and common tracking parameters."""
    parsed = urlparse(url)
    
    # Remove fragment
    clean_url = url.split('#')[0]
    
    # Remove common tracking parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'ref', 'source', 'campaign', '_ga', 'mc_cid'
    }
    
    query_params = []
    if parsed.query:
        for param in parsed.query.split('&'):
            if '=' in param:
                key = param.split('=')[0].lower()
                if key not in tracking_params:
                    query_params.append(param)
    
    if query_params:
        clean_url = clean_url.split('?')[0] + '?' + '&'.join(query_params)
    else:
        clean_url = clean_url.split('?')[0]
    
    return clean_url


def _looks_like_article(url: str) -> bool:
    """
    Determine if a URL looks like an article based on path patterns.
    
    Args:
        url: The URL to evaluate
        
    Returns:
        True if the URL appears to be an article
    """
    url_lower = url.lower()
    path = urlparse(url).path.lower()
    
    # Positive patterns - indicates likely article
    article_patterns = [
        r'/news/',
        r'/article/',
        r'/articles/',
        r'/story/',
        r'/stories/',
        r'/blog/',
        r'/post/',
        r'/posts/',
        r'/review/',
        r'/reviews/',
        r'/opinion/',
        r'/opinions/',
        r'/feature/',
        r'/features/',
        r'/analysis/',
        r'/commentary/',
        r'/editorial/',
        r'/20\d{2}/',  # Year in path (2020, 2021, etc.)
        r'/\d{4}/\d{2}/',  # YYYY/MM pattern
        r'/\d{4}-\d{2}-\d{2}/',  # YYYY-MM-DD pattern
        r'[-_]\w+[-_]\w+[-_]\w+',  # Long slug patterns
    ]
    
    # Negative patterns - excludes non-articles
    exclude_patterns = [
        r'/live[/?]',
        r'/video[/?]',
        r'/videos[/?]',
        r'/photo[/?]',
        r'/photos[/?]',
        r'/gallery[/?]',
        r'/galleries[/?]',
        r'/tag[/?]',
        r'/tags[/?]',
        r'/category[/?]',
        r'/categories[/?]',
        r'/topic[/?]',
        r'/topics[/?]',
        r'/author[/?]',
        r'/authors[/?]',
        r'/search[/?]',
        r'/contact[/?]',
        r'/about[/?]',
        r'/privacy[/?]',
        r'/terms[/?]',
        r'/subscribe[/?]',
        r'/newsletter[/?]',
        r'/rss[/?]',
        r'/sitemap',
        r'/api[/?]',
        r'/feed[/?]',
        r'\.xml$',
        r'\.rss$',
        r'\.json$',
        r'\.pdf$',
    ]
    
    # Check exclude patterns first
    for pattern in exclude_patterns:
        if re.search(pattern, url_lower):
            return False
    
    # Check positive patterns
    for pattern in article_patterns:
        if re.search(pattern, url_lower):
            return True
    
    # Additional heuristics
    # Long paths with multiple segments often indicate articles
    path_segments = [seg for seg in path.split('/') if seg and seg != '']
    if len(path_segments) >= 3:
        # Check if path has date-like or slug-like segments
        for segment in path_segments:
            # Date patterns
            if re.match(r'20\d{2}', segment) or re.match(r'\d{4}-\d{2}-\d{2}', segment):
                return True
            # Long meaningful slugs (not just single words)
            if len(segment) > 10 and '-' in segment:
                return True
    
    # URLs with meaningful slugs (long, hyphenated) are likely articles
    if len(path) > 20 and path.count('-') >= 2:
        return True
    
    return False
