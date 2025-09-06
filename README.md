# Homepage Article Scraper

A **lightning-fast**, ultra-optimized scraper that fetches homepage articles with **world-class S3 performance** (148+ uploads/second).

## 🚀 **Performance Highlights**

- **⚡ Ultra-Fast S3 Uploads**: 148+ articles/second upload rate with AWS CRT
- **🔥 Blazing Speed**: 50 articles scraped in ~14 seconds (vs 60+ seconds before)
- **🎯 Optimized Pipeline**: Connection pooling, batch uploads, concurrent processing
- **☁️ Cloud-Native**: Direct S3 upload with zero local storage overhead

## ✨ **Features**

- **🚀 Ultra-fast crawling**: Optimized Scrapy with 64 concurrent requests
- **🧠 Smart article detection**: Advanced heuristic filtering
- **📄 Robust content extraction**: trafilatura with BeautifulSoup fallback
- **⚡ Optional AI summarization**: Local BERT/BART (can be disabled for speed)
- **🖥️ Multiple interfaces**: Modern GUI, CLI, and remote execution
- **☁️ Cloud storage**: Ultra-fast S3 upload with AWS CRT optimization
- **📊 Structured output**: JSON files + CSV + summary reports

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

# Scraping Settings (OPTIMIZED for maximum speed)
CONCURRENT_REQUESTS=64
CONCURRENT_REQUESTS_PER_DOMAIN=32
DOWNLOAD_DELAY=0
MAX_ARTICLES=40
SUMMARY_ENABLED=false
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

## 🎯 **Performance & Optimization**

### **Ultra-Fast S3 Upload System**
- **AWS CRT Integration**: Native C++ performance with 50-connection pooling
- **Batch Processing**: Concurrent uploads with 8 optimized workers
- **Connection Reuse**: Single session across all uploads
- **Performance**: **148+ uploads/second** (vs 8-10/second standard)

### **Scraping Optimizations**
- **64 concurrent requests** (vs 32 standard)
- **Optimized timeouts**: 15s vs 30s for faster failures
- **AI summarization**: Disabled by default for maximum speed
- **Memory efficient**: 3GB limit with optimized queue management

### **EC2 Optimizations**
- **CPU performance mode**: Maximum processing power
- **Network optimization**: Enhanced TCP settings and buffers
- **Memory management**: Optimized for sustained high throughput
- **Instance recommendations**: c5.xlarge or better for maximum speed

## Troubleshooting

### Common Issues

- **Memory issues on small instances**: Set `SUMMARY_ENABLED=false` (default)
- **Rate limiting**: Increase `DOWNLOAD_DELAY` or reduce `CONCURRENT_REQUESTS`
- **S3 upload failures**: Check AWS credentials and bucket permissions
- **Slow uploads**: Ensure AWS CRT is installed: `pip install awscrt`
- **EC2 performance**: Use c5.xlarge or better for maximum speed

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
