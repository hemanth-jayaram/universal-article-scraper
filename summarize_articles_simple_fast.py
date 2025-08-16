#!/usr/bin/env python3
"""
SIMPLE FAST Article Summarizer using Facebook BART

This version focuses on reliable speed improvements without complex optimizations
that might cause hanging or compatibility issues.

Usage:
    python summarize_articles_simple_fast.py
    python summarize_articles_simple_fast.py --batch-size 4
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import multiprocessing as mp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_transformers_availability():
    """Check if transformers library is available."""
    try:
        from transformers import pipeline
        import torch
        logger.info(f"✅ PyTorch version: {torch.__version__}")
        return True
    except ImportError:
        logger.error("Transformers library not found. Install it with: pip install transformers torch")
        return False

def load_bart_model_simple():
    """Load BART model with simple optimizations."""
    try:
        from transformers import pipeline
        import torch
        
        logger.info("Loading Facebook BART model with simple optimizations...")
        
        # Use pipeline for simplicity and built-in optimizations
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            tokenizer="facebook/bart-large-cnn",
            device=-1  # CPU only for reliability
        )
        
        logger.info("✅ BART model loaded successfully!")
        return summarizer
        
    except Exception as e:
        logger.error(f"Failed to load BART model: {str(e)}")
        return None

def clean_text_for_summarization(text: str) -> str:
    """Clean and prepare text for summarization."""
    if not text:
        return ""
    
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate_summary_batch_simple(summarizer, contents: List[str], max_length: int = 150, min_length: int = 50, batch_size: int = 4) -> List[str]:
    """Generate summaries using simple batch processing."""
    summaries = []
    
    logger.info(f"Processing {len(contents)} articles in batches of {batch_size}...")
    
    # Process in smaller batches to avoid memory issues
    for i in range(0, len(contents), batch_size):
        batch_contents = contents[i:i + batch_size]
        batch_summaries = []
        
        logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(contents) + batch_size - 1)//batch_size} ({len(batch_contents)} articles)")
        
        # Process each article in the batch
        for j, content in enumerate(batch_contents):
            try:
                # Clean the content
                cleaned_content = clean_text_for_summarization(content)
                
                if not cleaned_content or len(cleaned_content.strip()) < 100:
                    summary = "Content too short for meaningful summarization."
                else:
                    # Truncate content for BART's token limit
                    max_input_length = 800  # Conservative limit
                    if len(cleaned_content) > max_input_length:
                        cleaned_content = cleaned_content[:max_input_length] + "..."
                    
                    # Generate summary
                    logger.info(f"  📝 Summarizing article {j+1}/{len(batch_contents)} in batch {i//batch_size + 1}")
                    
                    result = summarizer(
                        cleaned_content,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False,
                        truncation=True
                    )
                    
                    summary = result[0]['summary_text'].strip()
                    if not summary.endswith('.'):
                        summary += '.'
                
                batch_summaries.append(summary)
                logger.info(f"  ✅ Article {j+1} summarized ({len(summary)} chars)")
                
            except Exception as e:
                logger.warning(f"  ❌ Failed to summarize article {j+1}: {str(e)}")
                # Fallback to extractive summary
                fallback_summary = generate_extractive_summary(content, 3)
                batch_summaries.append(fallback_summary)
        
        summaries.extend(batch_summaries)
        logger.info(f"✅ Batch {i//batch_size + 1} completed ({len(batch_summaries)} summaries)")
    
    return summaries

def generate_extractive_summary(content: str, max_sentences: int = 3) -> str:
    """Generate extractive summary as fallback."""
    if not content:
        return "No content available for summarization."
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if not sentences:
        return "Content could not be processed for summarization."
    
    # Take first few sentences as summary
    summary_sentences = sentences[:max_sentences]
    summary = '. '.join(summary_sentences)
    
    if not summary.endswith('.'):
        summary += '.'
    
    return summary

def load_json_files_parallel(json_files: List[Path], workers: int = 4) -> List[Tuple[Path, Dict]]:
    """Load JSON files in parallel."""
    def load_single_file(file_path: Path) -> Tuple[Path, Optional[Dict]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return file_path, data
        except Exception as e:
            logger.warning(f"Failed to load {file_path.name}: {e}")
            return file_path, None
    
    logger.info(f"Loading {len(json_files)} files with {workers} workers...")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(load_single_file, json_files))
    
    # Filter out failed loads
    valid_results = [(path, data) for path, data in results if data is not None]
    logger.info(f"Successfully loaded {len(valid_results)}/{len(json_files)} files")
    
    return valid_results

def is_actual_article(data: Dict) -> Tuple[bool, str]:
    """Determine if a JSON file contains an actual article vs category/tool/listing page."""
    title = data.get('title', '').lower()
    content = data.get('content', '')
    url = data.get('url', '').lower()
    author = data.get('author', '')
    
    # Normalize author field
    author_normalized = author.strip() if author else ''
    
    # DEFINITIVE NON-ARTICLE INDICATORS (immediate exclusion)
    definitive_non_articles = [
        # Policy/Legal pages
        'policy' in title and ('privacy' in title or 'cookie' in title),
        'terms of service' in title or 'terms and conditions' in title,
        
        # Live/Real-time pages
        'live score' in title or 'live cricket score' in title,
        'live updates' in title,
        'live blog' in title,
        
        # Tool/Service pages
        'calculator' in title,
        'checker' in title,
        'interactive map' in title,
        'charging stations map' in title,
        
        # Category/Listing pages
        'latest news on' in title,
        'latest movies' in title and 'list of' in title,
        'top 20' in title and ('movies' in title or 'films' in title),
        title.endswith(' news') and len(content) > 2000 and content.count(' - ') > 10,
        
        # Commercial pages - only filter obvious non-articles
        'lease deals' in title and len(content) < 500,  # Only if very short
        # Removed overly strict car-related filters
        
        # Category navigation pages
        'buying a car' == title.strip(),
        'selling a car' == title.strip(),
        'selling a van' == title.strip(),
        
        # Content patterns that indicate non-articles
        content.count('Other topics in this category') > 0,
        # Removed overly strict car-related content filters
        len(content) < 150,  # Reduced minimum for commercial content
    ]
    
    # Check definitive exclusions first
    if any(definitive_non_articles):
        return False, "Definitive non-article: Policy, tool, category, or commercial page"
    
    # STRONG ARTICLE INDICATORS
    strong_article_indicators = [
        # Author presence (different patterns for different sites)
        author_normalized and author_normalized.lower() not in ['null', 'none', ''],
        'desk' in author_normalized.lower(),  # TOI pattern: "TOI Lifestyle Desk"
        'global' in author_normalized.lower(),  # TOI pattern: "Global Sports Desk"
        len(author_normalized.split()) >= 2,  # Full names
        
        # Content quality indicators
        len(content) > 1000 and content.count('.') > 25,  # Substantial, sentence-rich content
        len(content) > 2000,  # Very substantial content
        
        # Article-style titles
        ': ' in title and len(title.split(':')) == 2,  # Clean title:subtitle format
        title.count('|') == 1 and 'news' in title,  # News article format: "Title | News Source"
        
        # Content type indicators
        bool('how to' in title or 'how' in title[:10]),
        bool('why' in title[:20]),
        bool('what' in title[:20] and '?' in title),
        bool('should i' in title),
        bool('vs' in title and len(content) > 800),
        bool('tips' in title and len(content) > 800),
        bool('guide' in title and len(content) > 800),
        bool('everything you need to know' in title),
        
        # Commercial/Blog content indicators
        bool('for sale' in title and len(content) > 800),  # Commercial listings with substantial content
        bool('deals' in title and len(content) > 600),     # Deal pages with good content
        bool('review' in title and len(content) > 500),    # Reviews
        bool('compare' in title and len(content) > 600),   # Comparison pages
        bool('lease' in title and len(content) > 600),     # Lease deals
        bool('used cars' in title and len(content) > 500), # Used car listings
        bool('news' in title and len(content) > 400),      # News articles
        bool('clean air zone' in title and len(content) > 300), # Location info
        
        # Specific content patterns
        bool(content.count('paragraph') == 0 and content.count('section') < 3),  # Not a template
        bool(content.count('http') < 5),  # Not a link collection
    ]
    
    # WEAK ARTICLE INDICATORS
    weak_article_indicators = [
        bool(len(content) > 500),
        bool(content.count('.') > 10),
        bool(not any(x in title for x in ['list', 'top 10', 'top 20', 'deals'])),
        bool('news' in url and len(content) > 800),
    ]
    
    # CONTENT ANALYSIS - Check if it reads like an article
    def analyze_content_structure():
        if len(content) < 200:  # Reduced minimum for commercial content
            return False, "Too short"
        
        sentences = content.split('.')
        if len(sentences) < 5:  # Reduced minimum for commercial content
            return False, "Too few sentences"
        
        # More flexible content analysis for commercial/blog sites
        navigation_words = content.lower().count('browse') + content.lower().count('select') + content.lower().count('filter')
        article_words = content.lower().count('however') + content.lower().count('therefore') + content.lower().count('although')
        
        # Allow more navigation language for commercial sites
        if navigation_words > article_words * 6:  # Further increased threshold
            return False, "Too much navigation language"
        
        return True, "Good content structure"
    
    content_analysis, content_reason = analyze_content_structure()
    
    # SCORING
    strong_score = sum(strong_article_indicators)
    weak_score = sum(weak_article_indicators)
    total_score = strong_score * 2 + weak_score  # Weight strong indicators more heavily
    
    # DECISION LOGIC
    if strong_score >= 3:
        return True, f"Strong article (score: {strong_score}): Multiple strong indicators"
    elif strong_score >= 2 and content_analysis:
        return True, f"Likely article (score: {strong_score}): Strong indicators + good content"
    elif strong_score >= 1 and weak_score >= 3 and content_analysis:
        return True, f"Probable article (total score: {total_score}): Combined indicators"
    elif author_normalized and len(content) > 1000 and content_analysis:
        return True, f"Article with author: {author_normalized[:30]}... and substantial content"
    elif not content_analysis:
        return False, f"Non-article: {content_reason}"
    elif total_score < 2:
        return False, f"Non-article: Low article score ({total_score})"
    else:
        return False, "Non-article: Insufficient article indicators"

def find_json_files(results_dir: Path) -> List[Path]:
    """Find all JSON files in results directory."""
    json_files = []
    
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        return json_files
    
    excluded_files = {'scrape_summary.json', 'summary.json', 'metadata.json'}
    excluded_extensions = {'.csv', '.txt', '.log', '.md', '.html', '.xml', '.yml', '.yaml'}
    
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            file_lower = file.lower()
            file_path = Path(root) / file
            
            if (file_lower.endswith('.json') and 
                not file.startswith('.') and 
                file_lower not in excluded_files and
                Path(file).suffix.lower() not in excluded_extensions):
                
                try:
                    # Quick validation
                    with open(file_path, 'r', encoding='utf-8') as f:
                        test_content = f.read(100)
                        if test_content.strip().startswith('{'):
                            json_files.append(file_path)
                except:
                    continue
    
    logger.info(f"Found {len(json_files)} JSON files")
    return json_files

def filter_articles_only(json_files: List[Path]) -> List[Path]:
    """Filter JSON files to only include actual articles."""
    articles = []
    filtered_out = []
    
    logger.info("🔍 Analyzing content to identify actual articles...")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            is_article, reason = is_actual_article(data)
            
            if is_article:
                articles.append(file_path)
                logger.info(f"✅ Article: {file_path.name} - {reason}")
            else:
                filtered_out.append(file_path)
                logger.info(f"❌ Filtered: {file_path.name} - {reason}")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not analyze {file_path.name}: {e}")
            filtered_out.append(file_path)
    
    logger.info("=" * 60)
    logger.info(f"📊 FILTERING RESULTS:")
    logger.info(f"✅ Articles to summarize: {len(articles)}")
    logger.info(f"❌ Non-articles filtered out: {len(filtered_out)}")
    logger.info(f"📋 Total files processed: {len(json_files)}")
    logger.info("=" * 60)
    
    if len(articles) == 0:
        logger.warning("⚠️  No articles found! All files were filtered out.")
        logger.warning("This might indicate overly strict filtering. Check the filtering logic.")
    
    return articles

def main():
    """Main function with simple optimizations."""
    parser = argparse.ArgumentParser(description="Simple Fast Article Summarizer using Facebook BART")
    parser.add_argument('--input', '-i', default='results', help='Input directory (default: results)')
    parser.add_argument('--output', '-o', default='summary', help='Output directory (default: summary)')
    parser.add_argument('--max-length', type=int, default=150, help='Maximum summary length (default: 150)')
    parser.add_argument('--min-length', type=int, default=50, help='Minimum summary length (default: 50)')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size for processing (default: 4)')
    parser.add_argument('--workers', type=int, default=min(4, mp.cpu_count()), help='Number of worker threads (default: 4)')
    parser.add_argument('--no-overwrite', action='store_true', help='Do not overwrite existing summary directory')
    
    args = parser.parse_args()
    
    # Set up paths
    results_dir = Path(args.input)
    summary_dir = Path(args.output)
    
    logger.info("🚀 Simple Fast Article Summarizer using Facebook BART")
    logger.info("=" * 60)
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Workers: {args.workers}")
    
    # Check dependencies
    if not check_transformers_availability():
        sys.exit(1)
    
    # Load model
    summarizer = load_bart_model_simple()
    if not summarizer:
        logger.error("Failed to load model")
        sys.exit(1)
    
    # Find and filter JSON files
    logger.info(f"Scanning directory: {results_dir.absolute()}")
    json_files = find_json_files(results_dir)
    if not json_files:
        logger.error("No valid JSON files found")
        sys.exit(1)
    
    # Filter to only actual articles
    article_files = filter_articles_only(json_files)
    if not article_files:
        logger.error("No articles found to summarize after filtering")
        logger.error("All files were identified as non-articles (category pages, tools, listings, etc.)")
        sys.exit(1)
    
    # Create summary directory
    if summary_dir.exists():
        if args.no_overwrite:
            logger.error(f"Summary directory exists: {summary_dir}")
            sys.exit(1)
        else:
            logger.info(f"Removing existing summary directory: {summary_dir}")
            shutil.rmtree(summary_dir)
    
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    # Load files in parallel
    start_time = time.time()
    file_data_pairs = load_json_files_parallel(article_files, args.workers)
    
    if not file_data_pairs:
        logger.error("No files could be loaded")
        sys.exit(1)
    
    # Extract contents for processing
    contents = []
    valid_pairs = []
    
    for file_path, data in file_data_pairs:
        content = data.get('content', '')
        if content:
            contents.append(content)
            valid_pairs.append((file_path, data))
        else:
            logger.warning(f"No content in {file_path.name}")
    
    if not contents:
        logger.error("No articles with content found")
        sys.exit(1)
    
    logger.info(f"Processing {len(contents)} articles with content...")
    
    # Generate summaries
    summaries = generate_summary_batch_simple(
        summarizer, contents, 
        args.max_length, args.min_length, args.batch_size
    )
    
    # Save results
    logger.info("Saving summarized articles...")
    saved_count = 0
    
    for i, (file_path, data) in enumerate(valid_pairs):
        if i < len(summaries):
            try:
                # Add summary to data
                data['summary'] = summaries[i]
                data['summarization_method'] = 'facebook_bart_large_cnn_simple_fast'
                data['summarization_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                data['original_content_length'] = len(data.get('content', ''))
                data['summary_length'] = len(summaries[i])
                
                # Determine output path
                relative_path = file_path.relative_to(results_dir)
                output_path = summary_dir / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                saved_count += 1
                logger.info(f"✅ Saved: {output_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to save {file_path.name}: {e}")
    
    # Final statistics
    elapsed_time = time.time() - start_time
    articles_per_second = saved_count / elapsed_time if elapsed_time > 0 else 0
    
    logger.info("=" * 60)
    logger.info("🎉 SIMPLE FAST SUMMARIZATION COMPLETE")
    logger.info(f"✅ Articles processed: {saved_count}")
    logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    logger.info(f"🚀 Speed: {articles_per_second:.2f} articles/second")
    logger.info(f"📁 Output directory: {summary_dir.absolute()}")
    
    if saved_count > 0:
        logger.info("🎉 Summarization completed successfully!")
    else:
        logger.error("No files were processed successfully")
        sys.exit(1)

if __name__ == "__main__":
    main()
