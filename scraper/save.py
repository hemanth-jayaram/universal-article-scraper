"""
File utilities for saving article data as JSON and CSV.
"""

import os
import json
import csv
import hashlib
import re
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Import S3 upload functionality
try:
    from .s3_upload import get_s3_uploader, is_s3_configured
    S3_AVAILABLE = True
except ImportError:
    logger.warning("S3 upload module not available")
    S3_AVAILABLE = False


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


def write_json_per_article(article_data: Dict[str, Any], output_dir: str, use_s3: bool = None) -> bool:
    """
    Write article data to individual JSON file and append to CSV.
    Can save to local filesystem or S3 based on configuration.
    
    Args:
        article_data: Dictionary containing article information
        output_dir: Directory to save files (for local) or S3 prefix
        use_s3: Force S3 usage (None = auto-detect from env)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate filename
        title = article_data.get('title', '')
        if title:
            filename = sanitize_filename(title)
        else:
            filename = generate_filename_from_url(article_data.get('url', ''))
        
        json_filename = f"{filename}.json"
        
        # Determine if we should use S3
        if use_s3 is None:
            use_s3 = S3_AVAILABLE and is_s3_configured()
        
        success = True
        
        if use_s3 and S3_AVAILABLE:
            # Upload to S3 ONLY - no local saving when use_s3=True
            logger.debug(f"Using S3-only mode for: {json_filename}")
            try:
                success = _upload_article_to_s3(article_data, json_filename, output_dir)
                if success:
                    logger.debug(f"✅ Uploaded to S3: {json_filename}")
                else:
                    logger.error(f"❌ Failed to upload to S3: {json_filename}")
                    # In S3-only mode, don't fall back to local saving
                    logger.error(f"S3 upload failed for: {json_filename} - no local fallback in S3-only mode")
            except Exception as e:
                logger.error(f"❌ Exception during S3 upload for {json_filename}: {e}")
                import traceback
                logger.error(f"S3 upload traceback: {traceback.format_exc()}")
                # In S3-only mode, don't fall back to local saving  
                logger.error(f"S3 upload exception for: {json_filename} - no local fallback in S3-only mode")
                success = False
        else:
            # Save locally only when not using S3
            logger.debug(f"Using local-only mode for: {json_filename}")
            success = _save_article_locally(article_data, json_filename, output_dir)
            if success:
                logger.debug(f"✅ Saved locally: {json_filename}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to save article data: {e}")
        return False


def _save_article_locally(article_data: Dict[str, Any], json_filename: str, output_dir: str) -> bool:
    """Save article locally to filesystem."""
    try:
        # Ensure output directory exists
        ensure_output_dir(output_dir)
        
        json_path = os.path.join(output_dir, json_filename)
        
        # Handle duplicate filenames
        counter = 1
        base_filename = json_filename.replace('.json', '')
        while os.path.exists(json_path):
            json_filename = f"{base_filename}-{counter}.json"
            json_path = os.path.join(output_dir, json_filename)
            counter += 1
        
        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)
        
        # Append to CSV
        csv_success = _append_to_csv(article_data, output_dir)
        
        return csv_success
        
    except Exception as e:
        logger.error(f"Failed to save article locally: {e}")
        return False


def _upload_article_to_s3(article_data: Dict[str, Any], json_filename: str, s3_prefix: str) -> bool:
    """Upload article to S3."""
    try:
        logger.debug(f"Attempting to upload {json_filename} to S3 with prefix: {s3_prefix}")
        uploader = get_s3_uploader(prefix=s3_prefix)
        if not uploader:
            logger.error("S3 uploader not available")
            return False
        
        logger.debug(f"S3 uploader created for bucket: {uploader.bucket_name}")
        
        # Upload JSON
        json_success = uploader.upload_article_json(article_data, json_filename)
        logger.debug(f"JSON upload result for {json_filename}: {json_success}")
        
        # Also maintain CSV functionality for S3
        if json_success:
            csv_success = _upload_csv_to_s3(article_data, uploader)
            logger.debug(f"CSV upload result for {json_filename}: {csv_success}")
            return csv_success
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to upload article to S3: {e}")
        import traceback
        logger.error(f"S3 upload traceback: {traceback.format_exc()}")
        return False


# Global variable to store CSV content for S3 uploads
_s3_csv_content = []
_s3_csv_headers_written = False


def _upload_csv_to_s3(article_data: Dict[str, Any], uploader) -> bool:
    """Upload article data to S3 CSV file (accumulated and uploaded periodically)."""
    global _s3_csv_content, _s3_csv_headers_written
    
    try:
        # CSV field names
        fieldnames = ['title', 'url', 'author', 'published_date', 'content', 'summary']
        
        # Prepare row data
        row_data = {}
        for field in fieldnames:
            value = article_data.get(field, '')
            # Clean content for CSV (remove newlines)
            if field in ['content', 'summary'] and value:
                value = ' '.join(value.split())  # Normalize whitespace
            row_data[field] = value or ''
        
        # Add to accumulated CSV content
        if not _s3_csv_headers_written:
            # Create CSV headers
            import io
            import csv
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            _s3_csv_content.append(output.getvalue())
            _s3_csv_headers_written = True
        
        # Add data row
        import io
        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writerow(row_data)
        _s3_csv_content.append(output.getvalue())
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to prepare CSV data for S3: {e}")
        return False


def finalize_s3_csv_upload(uploader, filename: str = "all_articles.csv") -> bool:
    """Upload the accumulated CSV content to S3."""
    global _s3_csv_content
    
    try:
        if not _s3_csv_content:
            logger.warning("No CSV content to upload to S3")
            return True
        
        # Combine all CSV content
        csv_content = ''.join(_s3_csv_content)
        
        # Upload to S3
        success = uploader.upload_csv_content(csv_content, filename)
        
        if success:
            logger.info(f"Successfully uploaded CSV to S3: {filename}")
            # Clear accumulated content
            _s3_csv_content = []
            _s3_csv_headers_written = False
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to upload CSV to S3: {e}")
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


def create_summary_report(output_dir: str, homepage_url: str, total_found: int, processed: int, saved: int, elapsed_time: float, use_s3: bool = None) -> str:
    """
    Create a summary report of the scraping session.
    
    Args:
        output_dir: Output directory path or S3 prefix
        homepage_url: The scraped homepage URL
        total_found: Total articles found
        processed: Articles processed
        saved: Articles successfully saved
        elapsed_time: Time taken in seconds
        use_s3: Force S3 usage (None = auto-detect from env)
        
    Returns:
        Path to the summary report file or S3 URL
    """
    try:
        # Determine if we should use S3
        if use_s3 is None:
            use_s3 = S3_AVAILABLE and is_s3_configured()
        
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
            'storage_location': f"S3 bucket: {output_dir}" if use_s3 else f"Local directory: {output_dir}",
            'files_created': {
                'json_files': saved,
                'csv_file': 'all_articles.csv'
            }
        }
        
        if use_s3 and S3_AVAILABLE:
            # Upload to S3
            uploader = get_s3_uploader(prefix=output_dir)
            if uploader:
                success = uploader.upload_summary_report(report_data, 'scrape_summary.json')
                if success:
                    s3_url = uploader.get_upload_url('scrape_summary.json')
                    logger.info(f"Summary report uploaded to S3: {s3_url}")
                    return s3_url
                else:
                    logger.error("Failed to upload summary report to S3")
                    return ""
            else:
                logger.error("S3 uploader not available for summary report")
                return ""
        else:
            # Save locally
            summary_path = os.path.join(output_dir, 'scrape_summary.json')
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Summary report saved: {summary_path}")
            return summary_path
        
    except Exception as e:
        logger.error(f"Failed to create summary report: {e}")
        return ""
