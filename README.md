# Homepage Article Scraper

A fast, reliable scraper that fetches homepage articles and generates local BERT/BART summaries.

## Features

- **Fast crawling**: Uses Scrapy with optimized settings for speed
- **Smart article detection**: Heuristic filtering to identify article links
- **Robust content extraction**: trafilatura with BeautifulSoup fallback
- **Local summarization**: Uses sshleifer/distilbart-cnn-12-6 (no external APIs)
- **Dual interface**: CLI and local FastAPI web UI
- **Structured output**: Individual JSON files + combined CSV

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

### CLI Interface

```bash
source venv/bin/activate
python run.py "https://www.bbc.com/news" --out output
```

### Web UI Interface

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://<EC2_PUBLIC_IP>:8000/` in your browser.

**Note**: Ensure your EC2 security group allows port 8000, or use SSH tunnel:
```bash
ssh -L 8000:localhost:8000 -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
```

## Configuration

Environment variables (optional):
- `CONCURRENT_REQUESTS` (default: 32)
- `CONCURRENT_REQUESTS_PER_DOMAIN` (default: 16)
- `DOWNLOAD_DELAY` (default: 0)
- `MAX_ARTICLES` (default: 40)
- `SUMMARY_ENABLED` (default: true)

## Output Structure

```
output/
├── article-title-1.json
├── article-title-2.json
├── ...
└── all_articles.csv
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

- If memory is tight on t2.micro, set `SUMMARY_ENABLED=false`
- For rate limiting issues, increase `DOWNLOAD_DELAY`
- Check logs for specific extraction failures
