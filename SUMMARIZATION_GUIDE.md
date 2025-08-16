# Article Summarization Guide

This guide explains how to use the article summarization functionality to create summaries of your scraped articles using Facebook's BART model.

## Overview

The summarization feature processes all JSON files in your `results` folder and creates summarized versions using Facebook's BART-large-CNN model. Each summarized article maintains the same format as the original but includes an additional summary section.

## Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install transformers torch
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process all articles in the results folder
python summarize_articles.py
```

This will:
- Read all JSON files from the `results` folder
- Generate summaries using Facebook BART
- Save summarized articles to the `summary` folder

### Advanced Usage

```bash
# Specify custom input and output directories
python summarize_articles.py --input results --output my_summaries

# Customize summary length
python summarize_articles.py --max-length 200 --min-length 75

# Prevent overwriting (optional - by default it overwrites)
python summarize_articles.py --no-overwrite

# Full example with all options
python summarize_articles.py --input results --output summaries --max-length 150 --min-length 50
```

### Windows Batch Script

For convenience, you can use the provided batch script:

```cmd
summarize.bat
```

This script will:
1. Activate the virtual environment
2. Check prerequisites
3. Run the summarization
4. Display results

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input`, `-i` | Input directory containing JSON files | `results` |
| `--output`, `-o` | Output directory for summarized files | `summary` |
| `--max-length` | Maximum summary length in tokens | `150` |
| `--min-length` | Minimum summary length in tokens | `50` |
| `--no-overwrite` | Do not overwrite existing summary directory | `False` (default: overwrite) |

## Output Format

Each summarized article will have the same format as the original, plus these additional fields:

```json
{
  "title": "Original article title",
  "author": "Original author",
  "published_date": "Original date",
  "content": "Original full content",
  "url": "Original URL",
  "summary": "Generated summary using Facebook BART",
  "summarization_method": "facebook_bart_large_cnn",
  "summarization_timestamp": "2025-01-16 14:30:45",
  "original_content_length": 1234,
  "summary_length": 156
}
```

## Features

### Facebook BART Integration
- Uses Facebook's BART-large-CNN model
- Produces high-quality abstractive summaries
- Automatically handles text cleaning and preprocessing

### Fallback Mechanism
- If BART fails, uses extractive summarization
- Ensures every article gets a summary
- Graceful error handling

### Directory Structure Preservation
- Maintains the same folder structure as input
- Processes nested directories automatically
- Automatically excludes CSV files, summary files, and other non-article files

### File Filtering
- **Includes**: Only valid JSON files containing article data
- **Excludes**: CSV files (like `all_articles.csv`), summary files, metadata files
- **Validates**: Checks file content to ensure it's valid JSON format
- **Safe**: Won't process corrupted or non-article files

### Comprehensive Logging
- Detailed progress information
- Error reporting with specific file names
- Summary statistics at completion

## Troubleshooting

### Memory Issues
If you encounter memory allocation errors:

1. **Reduce batch size**: The script processes one file at a time to minimize memory usage
2. **Use CPU only**: The script is configured to use CPU by default
3. **Update PyTorch**: Make sure you have compatible versions:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

### Missing Dependencies
If you get import errors:

```bash
pip install transformers torch
```

### No Articles Found
Make sure your results directory contains JSON files:
- Check that articles were successfully scraped
- Verify the input directory path
- Ensure JSON files are not corrupted

## Performance

- **Processing Speed**: ~2-5 seconds per article (depending on length)
- **Memory Usage**: ~1-2GB RAM with BART model loaded
- **File Size**: Summarized files are slightly larger due to additional metadata

## Examples

### Process Recent Scraping Results
```bash
# After scraping carwow.co.uk
python summarize_articles.py --input results --output car_summaries
```

### Quick Summaries
```bash
# Generate shorter summaries
python summarize_articles.py --max-length 100 --min-length 30
```

### Batch Processing
```bash
# Process multiple result directories
python summarize_articles.py --input results/output_20250816_154344_154409 --output summaries/car_articles
```

## Integration with Scraping Workflow

Your complete workflow now becomes:

1. **Scrape articles**:
   ```bash
   .\scripts\run_remote_simple.ps1 -Ip "54.82.140.246" -Key "C:\Users\heman\Downloads\key-scraper.pem" -Url "https://www.carwow.co.uk/editorial/news"
   ```

2. **Summarize articles**:
   ```bash
   python summarize_articles.py
   ```

3. **Review results**:
   - Original articles: `results/` folder
   - Summarized articles: `summary/` folder

## Tips

- **Run summarization after each scraping session** for best organization
- **Use meaningful output directory names** for different topics
- **Check the logs** if any articles fail to process
- **Keep original articles** - summarization creates copies, doesn't modify originals
