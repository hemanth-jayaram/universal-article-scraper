# S3 Upload Configuration for Article Scraper

This document explains how to configure the article scraper to upload articles directly to an S3 bucket instead of saving them locally.

## Prerequisites

1. **AWS Account**: You need an AWS account with S3 access
2. **S3 Bucket**: Create a dedicated S3 bucket for article storage
3. **AWS Credentials**: Configure AWS credentials on your system
4. **boto3 Library**: Install boto3 Python library

## Installation

```bash
pip install boto3
```

## Configuration

### 1. Environment Variables

Create a `.env` file in your project root or set these environment variables:

```bash
# Enable S3 upload
S3_UPLOAD_ENABLED=true

# S3 Configuration
S3_BUCKET_NAME=your-article-scraper-bucket
AWS_REGION=us-east-1

# AWS Credentials (choose one method)
# Method 1: Environment variables
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Method 2: Use AWS credentials file or IAM role (recommended)
```

### 2. AWS Credentials Setup

Choose one of these methods:

#### Method A: AWS Credentials File (Recommended)
```bash
aws configure
```

#### Method B: Environment Variables
Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your `.env` file

#### Method C: IAM Role (For EC2 instances)
Attach an IAM role with S3 permissions to your EC2 instance

### 3. Required S3 Permissions

Your AWS credentials need these S3 permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Usage

Once configured, the scraper will automatically:

1. **Upload articles to S3** instead of saving locally
2. **Skip the download step** in the PowerShell script
3. **Organize files** in S3 with timestamp-based prefixes

### File Structure in S3

```
s3://your-bucket/
├── articles/
│   └── 20231215_143022/
│       ├── article-1.json
│       ├── article-2.json
│       ├── ...
│       ├── all_articles.csv
│       └── scrape_summary.json
```

### Running the Scraper

No changes needed to your GUI usage! Just click the "Scrape" button as usual.

The GUI will show:
- "🚀 Using S3 upload for articles" in the output
- S3 bucket information in the summary
- No local download messages

## Troubleshooting

### Common Issues

1. **"S3 uploader not available"**
   - Install boto3: `pip install boto3`
   - Check your .env file configuration

2. **"AWS credentials not found"**
   - Run `aws configure` or set environment variables
   - Verify credentials with: `aws s3 ls`

3. **"Access Denied"**
   - Check S3 bucket permissions
   - Verify IAM user/role has required permissions
   - Ensure bucket name is correct

### Testing S3 Configuration

```python
python -c "
from scraper.s3_upload import is_s3_configured, get_s3_uploader
print(f'S3 Configured: {is_s3_configured()}')
if is_s3_configured():
    uploader = get_s3_uploader()
    print(f'S3 Bucket: {uploader.bucket_name}')
    print(f'AWS Region: {uploader.region}')
"
```

### Accessing Uploaded Files

#### AWS CLI
```bash
# List all uploaded sessions
aws s3 ls s3://your-bucket-name/articles/

# List files from a specific session
aws s3 ls s3://your-bucket-name/articles/20231215_143022/

# Download a specific file
aws s3 cp s3://your-bucket-name/articles/20231215_143022/all_articles.csv ./
```

#### AWS Console
1. Open AWS S3 Console
2. Navigate to your bucket
3. Browse to `articles/` folder
4. Select the timestamp folder for your scraping session

## Switching Back to Local Storage

To disable S3 upload and return to local file storage:

1. Set `S3_UPLOAD_ENABLED=false` in your `.env` file, or
2. Remove the `S3_UPLOAD_ENABLED` environment variable entirely

The scraper will automatically fall back to local file storage.
