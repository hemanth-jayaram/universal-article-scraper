"""
Simple environment variable loader for .env files.
"""

import os
from pathlib import Path


def load_env_file(env_file: str = '.env') -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable if not already set
                    if key and key not in os.environ:
                        os.environ[key] = value
                        
    except Exception as e:
        print(f"Warning: Failed to load .env file: {e}")


def is_s3_enabled() -> bool:
    """
    Check if S3 upload is enabled.
    
    Returns:
        True if S3 upload is enabled, False otherwise
    """
    # Load .env file if it exists
    load_env_file()
    
    return os.getenv('S3_UPLOAD_ENABLED', 'false').lower() == 'true'


if __name__ == "__main__":
    # Example usage
    load_env_file()
    print(f"S3 Upload Enabled: {is_s3_enabled()}")
    print(f"S3 Bucket: {os.getenv('S3_BUCKET_NAME', 'Not set')}")
    print(f"AWS Region: {os.getenv('AWS_REGION', 'Not set')}")
