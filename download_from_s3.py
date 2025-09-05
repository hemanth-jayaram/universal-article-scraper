#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download files from S3 bucket to local results directory
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    try:
        # Load environment variables
        try:
            from load_env import load_env_file
            load_env_file()
            print("Environment loaded")
        except Exception as e:
            print(f"Warning: Could not load .env: {e}")
        
        # Import S3 modules
        try:
            from scraper.s3_upload import get_s3_uploader
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as e:
            print(f"ERROR: S3 modules not available: {e}")
            print("Please install boto3: pip install boto3")
            return False
        
        # Get S3 configuration
        bucket_name = os.getenv('S3_BUCKET_NAME')
        if not bucket_name:
            print('ERROR: S3_BUCKET_NAME not configured')
            return False
        
        print(f'Connecting to S3 bucket: {bucket_name}')
        s3_client = boto3.client('s3')
        
        # List all available prefixes (sessions)
        print('Finding available scraping sessions...')
        try:
            # First try the articles/ structure
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='articles/',
                Delimiter='/'
            )
            
            if 'CommonPrefixes' in response and response['CommonPrefixes']:
                # Found sessions in articles/ structure
                prefixes = [p['Prefix'] for p in response['CommonPrefixes']]
                latest_prefix = sorted(prefixes)[-1]  # Most recent timestamp
                print(f'Found sessions in articles/ structure')
            else:
                # Try direct timestamp structure (output_YYYYMMDD_HHMMSS/)
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Delimiter='/'
                )
                
                if 'CommonPrefixes' not in response:
                    print('ERROR: No scraping sessions found in S3')
                    return False
                
                # Filter for output_ prefixes
                all_prefixes = [p['Prefix'] for p in response['CommonPrefixes']]
                output_prefixes = [p for p in all_prefixes if p.startswith('output_')]
                
                if not output_prefixes:
                    print('ERROR: No output sessions found in S3')
                    return False
                
                latest_prefix = sorted(output_prefixes)[-1]  # Most recent timestamp
                prefixes = output_prefixes
                print(f'Found sessions in direct structure')
                
        except Exception as e:
            print(f'ERROR: Could not access bucket {bucket_name}: {e}')
            return False
        
        print(f'Found {len(prefixes)} sessions, downloading latest: {latest_prefix}')
        
        # List files in the latest session
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=latest_prefix
            )
        except Exception as e:
            print(f'ERROR: Could not list files in {latest_prefix}: {e}')
            return False
        
        if 'Contents' not in response:
            print('ERROR: No files found in latest session')
            return False
        
        files = response['Contents']
        print(f'Found {len(files)} files to download')
        
        # Create local results directory
        local_dir = Path('results')
        local_dir.mkdir(exist_ok=True)
        
        # Download each file
        downloaded_count = 0
        for i, file_obj in enumerate(files):
            key = file_obj['Key']
            filename = Path(key).name
            local_path = local_dir / filename
            
            print(f'Downloading {filename} ({i+1}/{len(files)})')
            
            try:
                s3_client.download_file(bucket_name, key, str(local_path))
                print(f'SUCCESS: Downloaded {filename}')
                downloaded_count += 1
            except Exception as e:
                print(f'ERROR: Failed to download {filename}: {e}')
        
        print(f'S3 download completed! Downloaded {downloaded_count}/{len(files)} files')
        print(f'Files saved to: {local_dir.absolute()}')
        return True
        
    except Exception as e:
        print(f'FATAL ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
