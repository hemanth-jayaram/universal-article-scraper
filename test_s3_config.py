#!/usr/bin/env python3
"""
Test script to validate S3 configuration for the article scraper.
"""

import os
import sys
from pathlib import Path

def test_s3_configuration():
    """Test S3 configuration and connectivity."""
    
    print("🧪 Testing S3 Configuration for Article Scraper")
    print("=" * 60)
    
    # Load environment variables
    try:
        from load_env import load_env_file
        load_env_file()
        print("✅ Environment variables loaded from .env file")
    except ImportError:
        print("⚠️  load_env module not available, using system environment variables")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    print()
    
    # Check basic configuration
    print("📋 Configuration Check:")
    s3_enabled = os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'
    bucket_name = os.getenv('S3_BUCKET_NAME')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"   S3 Upload Enabled: {s3_enabled}")
    print(f"   S3 Bucket Name: {bucket_name or 'Not set'}")
    print(f"   AWS Region: {aws_region}")
    
    if not s3_enabled:
        print("\n❌ S3 upload is disabled (S3_UPLOAD_ENABLED=false)")
        print("   To enable S3 upload, set S3_UPLOAD_ENABLED=true in your .env file")
        return False
    
    if not bucket_name:
        print("\n❌ S3 bucket name not configured")
        print("   Set S3_BUCKET_NAME in your .env file")
        return False
    
    print()
    
    # Test boto3 import
    print("📦 Dependencies Check:")
    try:
        import boto3
        print("✅ boto3 library is available")
    except ImportError:
        print("❌ boto3 library not found")
        print("   Install it with: pip install boto3")
        return False
    
    # Test S3 uploader import
    try:
        from scraper.s3_upload import get_s3_uploader, is_s3_configured
        print("✅ S3 upload module is available")
    except ImportError as e:
        print(f"❌ S3 upload module not available: {e}")
        return False
    
    print()
    
    # Test S3 configuration
    print("🔧 S3 Configuration Test:")
    if not is_s3_configured():
        print("❌ S3 is not properly configured")
        return False
    
    print("✅ S3 configuration is valid")
    
    # Test S3 connectivity
    print("\n🌐 S3 Connectivity Test:")
    try:
        uploader = get_s3_uploader()
        if not uploader:
            print("❌ Could not create S3 uploader")
            return False
        
        print(f"✅ S3 client created successfully")
        print(f"   Bucket: {uploader.bucket_name}")
        print(f"   Region: {uploader.region}")
        print(f"   Prefix: {uploader.prefix}")
        
        # Test bucket access
        try:
            uploader.s3_client.head_bucket(Bucket=uploader.bucket_name)
            print("✅ S3 bucket is accessible")
        except Exception as e:
            print(f"❌ Cannot access S3 bucket: {e}")
            print("   Check bucket name and permissions")
            return False
        
    except Exception as e:
        print(f"❌ S3 connectivity test failed: {e}")
        print("   Check AWS credentials and network connectivity")
        return False
    
    print()
    
    # Test article upload
    print("📝 Test Article Upload:")
    try:
        test_article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "content": "This is a test article for S3 upload validation.",
            "summary": "Test article summary",
            "author": "Test System",
            "published_date": "2023-12-15"
        }
        
        success = uploader.upload_article_json(test_article, "test-article.json")
        if success:
            print("✅ Test article uploaded successfully")
            print(f"   Location: {uploader.get_upload_url('test-article.json')}")
        else:
            print("❌ Test article upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Test article upload error: {e}")
        return False
    
    print()
    print("🎉 All S3 configuration tests passed!")
    print("🚀 Your scraper is ready to upload articles to S3")
    
    return True


def main():
    """Main test function."""
    try:
        success = test_s3_configuration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
