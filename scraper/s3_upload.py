"""
S3 upload utilities for saving article data to AWS S3.
"""

import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Uploader:
    """Handles uploading articles and data to S3 bucket."""
    
    def __init__(self, bucket_name: str = None, region: str = None, prefix: str = None):
        """
        Initialize S3 uploader.
        
        Args:
            bucket_name: S3 bucket name (defaults to env var S3_BUCKET_NAME)
            region: AWS region (defaults to env var AWS_REGION or 'us-east-1')
            prefix: S3 key prefix for uploaded files (defaults to timestamp)
        """
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided via parameter or S3_BUCKET_NAME environment variable")
        
        # Generate timestamp-based prefix if not provided
        if prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.prefix = f"articles/{timestamp}"
        else:
            self.prefix = prefix.strip('/')
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}, region: {self.region}")
        except NoCredentialsError:
            raise ValueError("AWS credentials not found. Please configure AWS credentials.")
        except Exception as e:
            raise ValueError(f"Failed to initialize S3 client: {e}")
    
    def upload_article_json(self, article_data: Dict[str, Any], filename: str) -> bool:
        """
        Upload article data as JSON to S3.
        
        Args:
            article_data: Dictionary containing article information
            filename: Filename for the JSON file (without path)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            # Create S3 key
            s3_key = f"{self.prefix}/{filename}"
            
            # Convert article data to JSON string
            json_content = json.dumps(article_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                ContentEncoding='utf-8'
            )
            
            logger.debug(f"Uploaded JSON to S3: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS error uploading JSON {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload JSON {filename}: {e}")
            return False
    
    def upload_csv_content(self, csv_content: str, filename: str = "all_articles.csv") -> bool:
        """
        Upload CSV content to S3.
        
        Args:
            csv_content: CSV content as string
            filename: Filename for the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure filename has .csv extension
            if not filename.endswith('.csv'):
                filename = f"{filename}.csv"
            
            # Create S3 key
            s3_key = f"{self.prefix}/{filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv',
                ContentEncoding='utf-8'
            )
            
            logger.debug(f"Uploaded CSV to S3: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS error uploading CSV {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload CSV {filename}: {e}")
            return False
    
    def upload_file(self, local_path: str, s3_filename: str = None) -> bool:
        """
        Upload a local file to S3.
        
        Args:
            local_path: Path to local file
            s3_filename: S3 filename (defaults to local filename)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            local_path = Path(local_path)
            
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return False
            
            # Use local filename if S3 filename not provided
            if s3_filename is None:
                s3_filename = local_path.name
            
            # Create S3 key
            s3_key = f"{self.prefix}/{s3_filename}"
            
            # Determine content type
            content_type = 'application/octet-stream'
            if local_path.suffix.lower() == '.json':
                content_type = 'application/json'
            elif local_path.suffix.lower() == '.csv':
                content_type = 'text/csv'
            elif local_path.suffix.lower() == '.txt':
                content_type = 'text/plain'
            
            # Upload file
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ContentEncoding': 'utf-8'
                }
            )
            
            logger.debug(f"Uploaded file to S3: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS error uploading file {local_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload file {local_path}: {e}")
            return False
    
    def upload_summary_report(self, report_data: Dict[str, Any], filename: str = "scrape_summary.json") -> bool:
        """
        Upload scraping summary report to S3.
        
        Args:
            report_data: Summary report data
            filename: Filename for the summary report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            # Create S3 key
            s3_key = f"{self.prefix}/{filename}"
            
            # Convert report data to JSON string
            json_content = json.dumps(report_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                ContentEncoding='utf-8'
            )
            
            logger.info(f"Uploaded summary report to S3: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS error uploading summary report: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload summary report: {e}")
            return False
    
    def get_upload_url(self, filename: str) -> str:
        """
        Get the S3 URL for an uploaded file.
        
        Args:
            filename: Name of the uploaded file
            
        Returns:
            S3 URL string
        """
        s3_key = f"{self.prefix}/{filename}"
        return f"s3://{self.bucket_name}/{s3_key}"
    
    def list_uploaded_files(self) -> list:
        """
        List all files uploaded with this prefix.
        
        Returns:
            List of S3 objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': f"s3://{self.bucket_name}/{obj['Key']}"
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"AWS error listing files: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []


def get_s3_uploader(bucket_name: str = None, region: str = None, prefix: str = None) -> Optional[S3Uploader]:
    """
    Factory function to create an S3Uploader instance.
    
    Args:
        bucket_name: S3 bucket name
        region: AWS region
        prefix: S3 key prefix
        
    Returns:
        S3Uploader instance or None if S3 is not configured
    """
    try:
        # Check if S3 upload is enabled
        s3_enabled = os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
        
        if not s3_enabled:
            logger.info("S3 upload is disabled (S3_UPLOAD_ENABLED=false)")
            return None
        
        return S3Uploader(bucket_name=bucket_name, region=region, prefix=prefix)
        
    except Exception as e:
        logger.error(f"Failed to create S3 uploader: {e}")
        return None


# Convenience functions for backward compatibility
def upload_article_to_s3(article_data: Dict[str, Any], filename: str, bucket_name: str = None) -> bool:
    """
    Convenience function to upload a single article to S3.
    
    Args:
        article_data: Article data dictionary
        filename: Filename for the JSON file
        bucket_name: S3 bucket name
        
    Returns:
        True if successful, False otherwise
    """
    uploader = get_s3_uploader(bucket_name=bucket_name)
    if uploader:
        return uploader.upload_article_json(article_data, filename)
    return False


def is_s3_configured() -> bool:
    """
    Check if S3 upload is properly configured.
    
    Returns:
        True if S3 is configured and enabled, False otherwise
    """
    try:
        s3_enabled = os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
        bucket_name = os.getenv('S3_BUCKET_NAME')
        
        return s3_enabled and bool(bucket_name)
        
    except Exception:
        return False
