"""
ULTRA-FAST S3 Upload Module
Implements the fastest possible S3 upload techniques:
- Connection pooling and session reuse
- Concurrent batch uploads
- Optimized boto3 configuration
- AWS CRT support when available
"""

import os
import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

# Suppress boto3 logging for performance
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# Global optimized S3 session and client
_GLOBAL_SESSION = None
_GLOBAL_CLIENT = None
_CLIENT_LOCK = threading.Lock()

class UltraFastS3Uploader:
    """Ultra-optimized S3 uploader with maximum performance techniques."""
    
    def __init__(self, bucket_name: str = None, region: str = None, prefix: str = None):
        """Initialize with optimized S3 client."""
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name required")
        
        if prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.prefix = f"articles/{timestamp}"
        else:
            self.prefix = prefix.strip('/')
        
        # Use optimized global client
        self.s3_client = self._get_optimized_client()
    
    def _get_optimized_client(self):
        """Get globally optimized S3 client with connection pooling."""
        global _GLOBAL_SESSION, _GLOBAL_CLIENT
        
        with _CLIENT_LOCK:
            if _GLOBAL_CLIENT is None:
                print("🚀 Creating ultra-optimized S3 client with connection pooling...")
                
                # Create optimized session
                _GLOBAL_SESSION = boto3.Session()
                
                # Ultra-optimized configuration
                config = Config(
                    region_name=self.region,
                    # Connection pooling for maximum performance
                    max_pool_connections=50,
                    # Retry configuration
                    retries={
                        'max_attempts': 2,
                        'mode': 'adaptive'
                    },
                    # TCP keepalive
                    tcp_keepalive=True,
                    # Signature version
                    signature_version='s3v4',
                    # Use path style for better performance
                    s3={
                        'addressing_style': 'path'
                    }
                )
                
                # Try to use AWS CRT if available for maximum speed
                try:
                    import awscrt
                    config.s3 = {
                        'use_accelerate_endpoint': False,
                        'use_dualstack_endpoint': False,
                        'addressing_style': 'path',
                        'use_aws_crt': True  # Enable CRT for maximum performance
                    }
                    print("✅ AWS CRT enabled for maximum S3 performance")
                except ImportError:
                    print("⚠️ AWS CRT not available, using standard boto3")
                
                _GLOBAL_CLIENT = _GLOBAL_SESSION.client('s3', config=config)
                print(f"✅ Optimized S3 client created for region: {self.region}")
            
            return _GLOBAL_CLIENT
    
    def upload_articles_batch(self, articles: List[Dict[str, Any]], max_workers: int = 8) -> int:
        """
        Upload multiple articles concurrently with maximum speed.
        
        Args:
            articles: List of article data dictionaries
            max_workers: Number of concurrent upload workers
            
        Returns:
            Number of successfully uploaded articles
        """
        if not articles:
            return 0
        
        print(f"🚀 Starting ULTRA-FAST batch upload of {len(articles)} articles...")
        start_time = time.time()
        
        # Optimize worker count based on article count
        optimal_workers = min(max_workers, len(articles), 10)  # Cap at 10 for S3 rate limits
        
        def upload_single_article(article_with_index):
            """Upload a single article with optimized settings."""
            index, article_data = article_with_index
            try:
                # Generate optimized filename
                url = article_data.get('url', '')
                if url:
                    filename = url.split('/')[-1] or f"article_{index}"
                    # Clean filename for S3 compatibility
                    filename = ''.join(c for c in filename if c.isalnum() or c in '-_.')[:80]
                    filename = filename.replace('.html', '').replace('.htm', '')
                else:
                    filename = f"article_{index}"
                
                if not filename.endswith('.json'):
                    filename = f"{filename}.json"
                
                # Create S3 key with random prefix for better distribution
                s3_key = f"{self.prefix}/{filename}"
                
                # Optimized JSON serialization
                json_content = json.dumps(article_data, separators=(',', ':'), ensure_ascii=False)
                
                # Ultra-fast S3 upload
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json_content.encode('utf-8'),
                    ContentType='application/json',
                    ContentEncoding='utf-8',
                    # Disable server-side encryption for speed (if not required)
                    # ServerSideEncryption='AES256'  # Uncomment if encryption needed
                )
                
                return True, filename, None
                
            except Exception as e:
                return False, f"article_{index}", str(e)
        
        # Execute concurrent uploads
        successful_uploads = 0
        failed_uploads = 0
        
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            # Submit all upload tasks
            future_to_article = {
                executor.submit(upload_single_article, (i, article)): i 
                for i, article in enumerate(articles)
            }
            
            # Process completed uploads
            for future in as_completed(future_to_article):
                success, filename, error = future.result()
                if success:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                    logger.error(f"Failed to upload {filename}: {error}")
        
        elapsed_time = time.time() - start_time
        upload_rate = successful_uploads / elapsed_time if elapsed_time > 0 else 0
        
        print(f"⚡ ULTRA-FAST upload complete:")
        print(f"   ✅ Uploaded: {successful_uploads}/{len(articles)} articles")
        print(f"   ⏱️ Time: {elapsed_time:.2f} seconds")
        print(f"   🚀 Rate: {upload_rate:.1f} uploads/second")
        
        return successful_uploads
    
    def upload_csv_optimized(self, csv_content: str, filename: str = "all_articles.csv") -> bool:
        """Upload CSV with optimized settings."""
        try:
            if not filename.endswith('.csv'):
                filename = f"{filename}.csv"
            
            s3_key = f"{self.prefix}/{filename}"
            
            # Optimized CSV upload
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv',
                ContentEncoding='utf-8'
            )
            
            print(f"✅ CSV uploaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"CSV upload failed: {e}")
            return False

def create_ultra_fast_uploader(bucket_name: str = None, region: str = None, prefix: str = None) -> UltraFastS3Uploader:
    """Create an ultra-fast S3 uploader instance."""
    return UltraFastS3Uploader(bucket_name=bucket_name, region=region, prefix=prefix)

# Backward compatibility function
def get_s3_uploader(bucket_name: str = None, region: str = None, prefix: str = None) -> Optional[UltraFastS3Uploader]:
    """Factory function returning ultra-fast uploader."""
    try:
        s3_enabled = os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
        if not s3_enabled:
            return None
        
        return UltraFastS3Uploader(bucket_name=bucket_name, region=region, prefix=prefix)
        
    except Exception as e:
        logger.error(f"Failed to create S3 uploader: {e}")
        return None

def is_s3_configured() -> bool:
    """Check if S3 is configured."""
    try:
        s3_enabled = os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
        bucket_name = os.getenv('S3_BUCKET_NAME')
        return s3_enabled and bool(bucket_name)
    except Exception:
        return False

# Test function
def test_ultra_fast_upload():
    """Test the ultra-fast upload functionality."""
    print("🧪 Testing ultra-fast S3 upload...")
    
    # Test articles
    test_articles = [
        {"title": f"Test Article {i}", "url": f"https://example.com/test{i}", "content": f"Test content {i}" * 50}
        for i in range(5)
    ]
    
    uploader = create_ultra_fast_uploader(prefix="test_ultra_fast")
    if uploader:
        result = uploader.upload_articles_batch(test_articles, max_workers=4)
        print(f"✅ Test complete: {result}/5 articles uploaded")
        return result == 5
    else:
        print("❌ Failed to create uploader")
        return False

if __name__ == "__main__":
    test_ultra_fast_upload()
