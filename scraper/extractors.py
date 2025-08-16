"""
Content extraction using trafilatura with BeautifulSoup fallback.
"""

import re
from typing import Dict, Optional, Any
from datetime import datetime
import logging

import trafilatura
from bs4 import BeautifulSoup
from scrapy.http import Response

logger = logging.getLogger(__name__)


def extract_article(response: Response) -> Optional[Dict[str, Any]]:
    """
    Extract article content from a webpage response.
    
    Uses trafilatura as primary extractor with BeautifulSoup fallback.
    
    Args:
        response: Scrapy response object
        
    Returns:
        Dictionary with extracted article data or None if extraction fails
    """
    if not response.body:
        logger.warning(f"Empty response body for {response.url}")
        return None
    
    # Check if this is actually HTML
    content_type = response.headers.get('content-type', b'').decode('utf-8', errors='ignore').lower()
    if 'html' not in content_type:
        logger.warning(f"Non-HTML content type for {response.url}: {content_type}")
        return None
    
    html_content = response.text
    
    # Try trafilatura first
    try:
        article_data = _extract_with_trafilatura(html_content, response.url)
        if article_data and article_data.get('content'):
            logger.debug(f"Successfully extracted with trafilatura: {response.url}")
            return article_data
    except Exception as e:
        logger.warning(f"Trafilatura extraction failed for {response.url}: {e}")
    
    # Fallback to BeautifulSoup
    try:
        article_data = _extract_with_beautifulsoup(html_content, response.url)
        if article_data and article_data.get('content'):
            logger.debug(f"Successfully extracted with BeautifulSoup: {response.url}")
            return article_data
    except Exception as e:
        logger.warning(f"BeautifulSoup extraction failed for {response.url}: {e}")
    
    logger.error(f"All extraction methods failed for {response.url}")
    return None


def _extract_with_trafilatura(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Extract article content using trafilatura.
    
    Args:
        html: HTML content as string
        url: The article URL
        
    Returns:
        Dictionary with extracted data or None
    """
    # Extract the main content
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_images=False,
        include_links=False
    )
    
    if not content or len(content.strip()) < 100:
        return None
    
    # Extract metadata
    metadata = trafilatura.extract_metadata(html)
    
    article_data = {
        'title': _clean_text(metadata.title) if metadata and metadata.title else None,
        'author': _clean_text(metadata.author) if metadata and metadata.author else None,
        'published_date': _format_date(metadata.date) if metadata and metadata.date else None,
        'content': _clean_text(content),
        'url': url
    }
    
    # If no title from metadata, try to extract from content
    if not article_data['title']:
        article_data['title'] = _extract_title_from_content(content)
    
    return article_data


def _extract_with_beautifulsoup(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
    Extract article content using BeautifulSoup with heuristic selectors.
    
    Args:
        html: HTML content as string
        url: The article URL
        
    Returns:
        Dictionary with extracted data or None
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract title
    title = _extract_title_bs(soup)
    
    # Extract author
    author = _extract_author_bs(soup)
    
    # Extract published date
    published_date = _extract_date_bs(soup)
    
    # Extract main content
    content = _extract_content_bs(soup)
    
    if not content or len(content.strip()) < 100:
        return None
    
    article_data = {
        'title': title,
        'author': author,
        'published_date': published_date,
        'content': content,
        'url': url
    }
    
    return article_data


def _extract_title_bs(soup: BeautifulSoup) -> Optional[str]:
    """Extract title using BeautifulSoup heuristics."""
    # Try various title selectors in order of preference
    title_selectors = [
        'h1.article-title',
        'h1.entry-title',
        'h1.post-title',
        'h1.headline',
        'h1[itemprop="headline"]',
        '.article-header h1',
        '.entry-header h1',
        '.post-header h1',
        'article h1',
        'h1'
    ]
    
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            title = _clean_text(element.get_text())
            if title and len(title) > 5:  # Reasonable title length
                return title
    
    # Fallback to page title, but clean it up
    title_tag = soup.find('title')
    if title_tag:
        title = _clean_text(title_tag.get_text())
        # Remove common site name patterns
        title = re.sub(r'\s*[-|]\s*.*$', '', title)
        if title and len(title) > 5:
            return title
    
    return None


def _extract_author_bs(soup: BeautifulSoup) -> Optional[str]:
    """Extract author using BeautifulSoup heuristics."""
    # Try various author selectors
    author_selectors = [
        '[itemprop="author"]',
        '[name="author"]',
        '.author',
        '.byline',
        '.by-author',
        '.article-author',
        '.post-author',
        '.entry-author',
        '[rel="author"]'
    ]
    
    for selector in author_selectors:
        elements = soup.select(selector)
        for element in elements:
            # Check for meta content attribute first
            author = element.get('content') or element.get_text()
            author = _clean_text(author)
            if author and len(author) < 100:  # Reasonable author name length
                return author
    
    return None


def _extract_date_bs(soup: BeautifulSoup) -> Optional[str]:
    """Extract published date using BeautifulSoup heuristics."""
    # Try various date selectors
    date_selectors = [
        'time[datetime]',
        '[itemprop="datePublished"]',
        '[property="article:published_time"]',
        '[name="article:published_time"]',
        '.published-date',
        '.publish-date',
        '.article-date',
        '.post-date',
        '.entry-date'
    ]
    
    for selector in date_selectors:
        elements = soup.select(selector)
        for element in elements:
            # Check for datetime attribute first
            date_str = element.get('datetime') or element.get('content') or element.get_text()
            date_str = _clean_text(date_str)
            if date_str:
                formatted_date = _format_date(date_str)
                if formatted_date:
                    return formatted_date
    
    return None


def _extract_content_bs(soup: BeautifulSoup) -> Optional[str]:
    """Extract main content using BeautifulSoup heuristics."""
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
        element.decompose()
    
    # Try various content selectors
    content_selectors = [
        'article .entry-content',
        'article .post-content',
        'article .article-content',
        '.entry-content',
        '.post-content',
        '.article-content',
        '.article-body',
        '.post-body',
        '[itemprop="articleBody"]',
        'article',
        '.content',
        'main'
    ]
    
    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            # Extract text from paragraphs
            paragraphs = element.find_all(['p', 'div', 'section'])
            if paragraphs:
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Filter out very short paragraphs
                        content_parts.append(text)
                
                if content_parts:
                    content = '\n\n'.join(content_parts)
                    if len(content) > 100:
                        return _clean_text(content)
    
    # Fallback: extract all paragraphs from body
    paragraphs = soup.find_all('p')
    if paragraphs:
        content_parts = []
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 30:  # Be more selective for fallback
                content_parts.append(text)
        
        if content_parts:
            content = '\n\n'.join(content_parts)
            if len(content) > 200:  # Higher threshold for fallback
                return _clean_text(content)
    
    return None


def _extract_title_from_content(content: str) -> Optional[str]:
    """Extract a title from the beginning of content."""
    if not content:
        return None
    
    # Take the first line/sentence as potential title
    lines = content.split('\n')
    first_line = lines[0].strip() if lines else ''
    
    # Use first sentence if first line is too long
    if len(first_line) > 100:
        sentences = first_line.split('. ')
        first_line = sentences[0] if sentences else first_line[:100]
    
    if len(first_line) > 10 and len(first_line) < 200:
        return first_line
    
    return None


def _clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common artifacts
    text = re.sub(r'\s*\n\s*', '\n', text)
    text = re.sub(r'\s*\t\s*', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{2,}', '--', text)
    
    return text.strip()


def _format_date(date_str: str) -> Optional[str]:
    """
    Format a date string to ISO format (YYYY-MM-DD).
    
    Args:
        date_str: Raw date string
        
    Returns:
        Formatted date string or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%B %d, %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%d %b %Y'
    ]
    
    # Clean the date string
    clean_date = re.sub(r'[^\w\s:/-]', '', date_str.strip())
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(clean_date, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Try parsing with just year extraction
    year_match = re.search(r'20\d{2}', clean_date)
    if year_match:
        return f"{year_match.group()}-01-01"  # Default to January 1st
    
    return None
