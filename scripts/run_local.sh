#!/usr/bin/env bash
#
# Local runner script for the Homepage Article Scraper
# Usage: ./scripts/run_local.sh "https://www.bbc.com/news" [output_dir]
#

set -e

# Check if URL is provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"<homepage_url>\" [output_dir]"
    echo "Example: $0 \"https://www.bbc.com/news\" output"
    exit 1
fi

URL="$1"
OUT="${2:-output}"

echo "Homepage Article Scraper - Local Runner"
echo "======================================"
echo "URL: $URL"
echo "Output: $OUT"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/.requirements_installed" ]; then
    echo "📦 Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.requirements_installed
    echo "✅ Requirements installed"
fi

# Run the scraper
echo "🚀 Starting scraper..."
python run.py "$URL" --out "$OUT"

echo ""
echo "✅ Scraping completed!"
echo "📁 Results saved to: $OUT"
echo ""
echo "To view results:"
echo "  - Individual articles: $OUT/*.json"
echo "  - Combined CSV: $OUT/all_articles.csv"
echo "  - Summary report: $OUT/scrape_summary.json"
