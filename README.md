# Homepage Article Scraper

A fast, reliable scraper that fetches homepage articles and generates local BERT/BART summaries with **S3 cloud storage integration**.

## Features

- **Fast crawling**: Uses Scrapy with optimized settings for speed
- **Smart article detection**: Heuristic filtering to identify article links
- **Robust content extraction**: trafilatura with BeautifulSoup fallback
- **Local summarization**: Uses sshleifer/distilbart-cnn-12-6 (no external APIs)
- **Multiple interfaces**: CLI, Desktop GUI, and local FastAPI web UI
- **Cloud storage**: Direct S3 upload with automatic download functionality
- **Structured output**: Individual JSON files + combined CSV + summary reports

## Quick Setup (Amazon Linux 2023)

```bash
# One-time setup
sudo yum update -y
sudo yum install -y git python3 python3-pip
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

### Desktop GUI (Recommended)

Launch the user-friendly desktop interface:
```bash
python scraper_gui.py
```

Features:
- **Easy scraping**: Paste URL and click "Start Scraping"
- **Remote execution**: Run scraper on EC2 instances
- **S3 integration**: Automatic upload to AWS S3 bucket
- **Download manager**: One-click download from S3 to local machine
- **Real-time monitoring**: Live progress updates and logs

### CLI Interface

```bash
source venv/bin/activate
python run.py "https://www.bbc.com/news" --out output
```

### Remote Execution

For running on AWS EC2 instances:
```bash
# Remote scraping with S3 upload
.\scripts\run_remote_simple.ps1 -Ip "YOUR_EC2_IP" -Key "path\to\key.pem" -Url "https://example.com"
```

## Configuration

### Environment Variables (`.env` file)

```bash
# S3 Configuration
S3_UPLOAD_ENABLED=true
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# AWS Credentials (optional - can use IAM roles)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key

# Scraping Settings
CONCURRENT_REQUESTS=32
CONCURRENT_REQUESTS_PER_DOMAIN=16
DOWNLOAD_DELAY=0
MAX_ARTICLES=40
SUMMARY_ENABLED=true
```

### S3 Setup

1. **Create S3 bucket** in AWS Console
2. **Configure credentials** (IAM roles recommended for EC2)
3. **Copy configuration**: `cp s3_config.example.env .env`
4. **Edit `.env`** with your bucket name and credentials
5. **Test configuration**: `python test_s3_config.py`

## Output Structure

### Local Storage
```
results/
├── article-title-1.json
├── article-title-2.json
├── ...
├── all_articles.csv
└── scrape_summary.json
```

### S3 Storage
```
s3://your-bucket/
└── articles/YYYYMMDD_HHMMSS/
    ├── article-title-1.json
    ├── article-title-2.json
    ├── ...
    ├── all_articles.csv
    └── scrape_summary.json
```

Each JSON file contains:
```json
{
  "title": "Article Title",
  "url": "https://example.com/article",
  "author": "Author Name",
  "published_date": "2024-01-01",
  "content": "Full article content...",
  "summary": "Generated summary..."
}
```

## Performance Notes

- Optimized for AWS EC2 with CPU-only processing
- Uses distilbart-cnn for fast, local summarization
- Configurable concurrency and limits
- Ignores robots.txt for comprehensive scraping
- Processes homepage + discovered articles only (depth=1)

## Troubleshooting

### Common Issues

- **Memory issues on t2.micro**: Set `SUMMARY_ENABLED=false`
- **Rate limiting**: Increase `DOWNLOAD_DELAY`
- **S3 upload failures**: Check AWS credentials and bucket permissions
- **Download not working**: Ensure boto3 is installed: `pip install boto3`
- **GUI Unicode errors**: Fixed in latest version - restart application

### S3 Permissions Required

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
        "s3:GetObject",
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

### Support Files

- `S3_SETUP.md`: Detailed S3 configuration guide
- `GUI_USER_GUIDE.md`: Complete GUI usage instructions
- `test_s3_config.py`: S3 configuration testing tool
