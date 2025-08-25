#!/usr/bin/env python3
"""
JSON to TXT Converter

Converts JSON article files from the results directory to readable TXT files
and saves them in a 'converted' directory.

Usage:
    python convert_json_to_txt.py
    python convert_json_to_txt.py --input results --output converted
"""

import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_json_files(input_dir: Path) -> List[Path]:
    """Find all JSON files in the input directory."""
    json_files = []
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return json_files
    
    # Exclude summary and metadata files
    excluded_files = {'scrape_summary.json', 'summary.json', 'metadata.json'}
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if (file.lower().endswith('.json') and 
                not file.startswith('.') and 
                file not in excluded_files):
                
                json_files.append(Path(root) / file)
    
    logger.info(f"Found {len(json_files)} JSON files to convert")
    return json_files


def convert_json_to_txt(json_file: Path, output_dir: Path) -> bool:
    """Convert a single JSON file to TXT format."""
    try:
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract fields
        title = data.get('title', 'Untitled')
        author = data.get('author', 'Unknown Author')
        published_date = data.get('published_date', 'Unknown Date')
        url = data.get('url', 'No URL')
        content = data.get('content', 'No content available')
        summary = data.get('summary', 'No summary available')
        
        # Create formatted text content
        txt_content = f"""Title: {title}
Author: {author}
Published: {published_date}
URL: {url}

{'='*80}
CONTENT
{'='*80}

{content}

{'='*80}
SUMMARY
{'='*80}

{summary}
"""
        
        # Generate output filename (same name but .txt extension)
        txt_filename = json_file.stem + '.txt'
        
        # Determine output path maintaining directory structure
        relative_path = json_file.relative_to(json_file.parents[len(json_file.parts) - 1])
        output_path = output_dir / relative_path.parent / txt_filename
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write TXT file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        logger.info(f"✅ Converted: {json_file.name} → {txt_filename}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to convert {json_file.name}: {e}")
        return False


def convert_files_parallel(json_files: List[Path], output_dir: Path, workers: int = 4) -> int:
    """Convert JSON files to TXT in parallel."""
    logger.info(f"Converting {len(json_files)} files with {workers} workers...")
    
    success_count = 0
    
    def convert_single(json_file: Path) -> bool:
        return convert_json_to_txt(json_file, output_dir)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(convert_single, json_files))
    
    success_count = sum(results)
    failed_count = len(json_files) - success_count
    
    logger.info(f"Conversion completed: {success_count} successful, {failed_count} failed")
    return success_count


def main():
    """Main function for JSON to TXT conversion."""
    parser = argparse.ArgumentParser(
        description="Convert JSON article files to readable TXT format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_json_to_txt.py
  python convert_json_to_txt.py --input results --output converted
  python convert_json_to_txt.py --input results/output_123 --output text_files --workers 8
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        default='results',
        help='Input directory containing JSON files (default: results)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='converted',
        help='Output directory for TXT files (default: converted)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of worker threads (default: 4)'
    )
    
    parser.add_argument(
        '--clear-output',
        action='store_true',
        help='Clear output directory before conversion'
    )
    
    args = parser.parse_args()
    
    # Set up paths
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    logger.info("📄 JSON to TXT Converter")
    logger.info("=" * 60)
    logger.info(f"Input directory: {input_dir.absolute()}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info(f"Workers: {args.workers}")
    
    # Find JSON files
    json_files = find_json_files(input_dir)
    if not json_files:
        logger.error("No JSON files found to convert")
        sys.exit(1)
    
    # Handle output directory
    if output_dir.exists() and args.clear_output:
        logger.info(f"Clearing existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert files
    start_time = time.time()
    success_count = convert_files_parallel(json_files, output_dir, args.workers)
    elapsed_time = time.time() - start_time
    
    # Final statistics
    conversion_rate = success_count / elapsed_time if elapsed_time > 0 else 0
    
    logger.info("=" * 60)
    logger.info("🎉 CONVERSION COMPLETE")
    logger.info(f"✅ Files converted: {success_count}/{len(json_files)}")
    logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    logger.info(f"🚀 Speed: {conversion_rate:.2f} files/second")
    logger.info(f"📁 Output directory: {output_dir.absolute()}")
    
    if success_count > 0:
        logger.info("🎯 Conversion completed successfully!")
        logger.info(f"📖 Text files are ready for reading at: {output_dir}")
    else:
        logger.error("❌ No files were converted successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
