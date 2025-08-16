"""
File utilities for saving article data as JSON and CSV.
"""

import os
import json
import csv
import hashlib
import re
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def ensure_output_dir(output_dir: str) -> None:
    """
    Ensure the output directory exists.
    
    Args:
        output_dir: Path to the output directory
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {output_dir}")


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """
    Sanitize a title to create a valid filename.
    
    Args:
        title: The article title
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename without extension
    """
    if not title:
        return "untitled"
    
    # Convert to lowercase and replace spaces with hyphens
    filename = title.lower()
    
    # Remove or replace problematic characters
    filename = re.sub(r'[^\w\s-]', '', filename)  # Keep only alphanumeric, spaces, hyphens
    filename = re.sub(r'\s+', '-', filename)      # Replace spaces with hyphens
    filename = re.sub(r'-+', '-', filename)       # Collapse multiple hyphens
    filename = filename.strip('-')                # Remove leading/trailing hyphens
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip('-')
    
    # Ensure we have something
    if not filename:
        filename = "untitled"
    
    return filename


def generate_filename_from_url(url: str) -> str:
    """
    Generate a filename from URL when title is not available.
    
    Args:
        url: The article URL
        
    Returns:
        Generated filename based on URL hash
    """
    # Create a short hash of the URL
    url_hash = hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]
    return f"article-{url_hash}"


def write_json_per_article(article_data: Dict[str, Any], output_dir: str) -> bool:
    """
    Write article data to individual JSON file and append to CSV.
    
    Args:
        article_data: Dictionary containing article information
        output_dir: Directory to save files
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        ensure_output_dir(output_dir)
        
        # Generate filename [[memory:6218210]]
        title = article_data.get('title', '')
        if title:
            filename = sanitize_filename(title)
        else:
            filename = generate_filename_from_url(article_data.get('url', ''))
        
        json_filename = f"{filename}.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Handle duplicate filenames
        counter = 1
        original_filename = filename
        while os.path.exists(json_path):
            filename = f"{original_filename}-{counter}"
            json_filename = f"{filename}.json"
            json_path = os.path.join(output_dir, json_filename)
            counter += 1
        
        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved JSON: {json_filename}")
        
        # Append to CSV
        csv_success = _append_to_csv(article_data, output_dir)
        
        return csv_success
        
    except Exception as e:
        logger.error(f"Failed to save article data: {e}")
        return False


def _append_to_csv(article_data: Dict[str, Any], output_dir: str) -> bool:
    """
    Append article data to the combined CSV file.
    
    Args:
        article_data: Dictionary containing article information
        output_dir: Directory containing the CSV file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        csv_path = os.path.join(output_dir, 'all_articles.csv')
        
        # CSV field names
        fieldnames = ['title', 'url', 'author', 'published_date', 'content', 'summary']
        
        # Check if CSV exists to determine if we need headers
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
                logger.debug("Created CSV with headers")
            
            # Prepare row data
            row_data = {}
            for field in fieldnames:
                value = article_data.get(field, '')
                # Clean content for CSV (remove newlines)
                if field in ['content', 'summary'] and value:
                    value = ' '.join(value.split())  # Normalize whitespace
                row_data[field] = value or ''
            
            writer.writerow(row_data)
            logger.debug("Appended to CSV")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to append to CSV: {e}")
        return False


def get_saved_articles_count(output_dir: str) -> int:
    """
    Get the count of saved JSON articles.
    
    Args:
        output_dir: Directory to count files in
        
    Returns:
        Number of JSON files in the directory
    """
    try:
        if not os.path.exists(output_dir):
            return 0
        
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        return len(json_files)
        
    except Exception as e:
        logger.error(f"Failed to count saved articles: {e}")
        return 0


def create_summary_report(output_dir: str, homepage_url: str, total_found: int, processed: int, saved: int, elapsed_time: float) -> str:
    """
    Create a summary report of the scraping session.
    
    Args:
        output_dir: Output directory path
        homepage_url: The scraped homepage URL
        total_found: Total articles found
        processed: Articles processed
        saved: Articles successfully saved
        elapsed_time: Time taken in seconds
        
    Returns:
        Path to the summary report file
    """
    try:
        report_data = {
            'homepage_url': homepage_url,
            'timestamp': json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}}),
            'statistics': {
                'total_articles_found': total_found,
                'articles_processed': processed,
                'articles_saved': saved,
                'success_rate': f"{(saved/processed*100):.1f}%" if processed > 0 else "0%",
                'elapsed_time_seconds': round(elapsed_time, 2)
            },
            'output_directory': output_dir,
            'files_created': {
                'json_files': saved,
                'csv_file': 'all_articles.csv'
            }
        }
        
        summary_path = os.path.join(output_dir, 'scrape_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved: {summary_path}")
        return summary_path
        
    except Exception as e:
        logger.error(f"Failed to create summary report: {e}")
        return ""
