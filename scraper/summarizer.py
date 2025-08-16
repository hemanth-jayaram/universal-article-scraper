"""
Local BERT/BART summarization using Hugging Face transformers.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global summarizer instance
_summarizer = None


def get_summarizer():
    """
    Get or initialize the summarization pipeline.
    
    Returns:
        The summarization pipeline instance
    """
    global _summarizer
    
    if _summarizer is None:
        try:
            from transformers import pipeline
            
            logger.info("Initializing summarization model: sshleifer/distilbart-cnn-12-6")
            _summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
                device=-1,  # CPU only
                tokenizer="sshleifer/distilbart-cnn-12-6"
            )
            logger.info("Summarization model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize summarizer: {e}")
            _summarizer = None
    
    return _summarizer


def summarize(
    text: str, 
    max_length: Optional[int] = None, 
    min_length: Optional[int] = None
) -> str:
    """
    Generate a summary of the given text using local BART model.
    
    Args:
        text: The text content to summarize
        max_length: Maximum length of summary (default from env or 160)
        min_length: Minimum length of summary (default from env or 60)
        
    Returns:
        Generated summary text or fallback summary if model fails
    """
    if not text or len(text.strip()) < 100:
        return text or "N/A"
    
    # Get configuration from environment
    if max_length is None:
        max_length = int(os.getenv('SUMMARY_MAX_LENGTH', 160))
    if min_length is None:
        min_length = int(os.getenv('SUMMARY_MIN_LENGTH', 60))
    
    # Check if summarization is enabled
    if os.getenv('SUMMARY_ENABLED', 'true').lower() == 'false':
        return _fallback_summary(text, max_length)
    
    summarizer = get_summarizer()
    if not summarizer:
        logger.warning("Summarizer not available, using fallback")
        return _fallback_summary(text, max_length)
    
    try:
        # Truncate text to model's maximum input length (~1024 tokens)
        # Rough estimate: 1 token ≈ 4 characters
        max_input_chars = 4000
        if len(text) > max_input_chars:
            text = text[:max_input_chars]
            logger.debug("Truncated input text for summarization")
        
        # Generate summary
        result = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,  # Deterministic output
            truncation=True
        )
        
        if result and len(result) > 0:
            summary = result[0]['summary_text'].strip()
            if summary:
                logger.debug(f"Generated summary: {len(summary)} chars")
                return summary
        
        logger.warning("Empty summary generated, using fallback")
        return _fallback_summary(text, max_length)
        
    except Exception as e:
        logger.warning(f"Summarization failed: {e}, using fallback")
        return _fallback_summary(text, max_length)


def _fallback_summary(text: str, max_chars: int = 160) -> str:
    """
    Create a fallback summary by extracting key sentences.
    
    Args:
        text: The original text
        max_chars: Maximum characters for summary
        
    Returns:
        Simple extractive summary
    """
    if not text:
        return "N/A"
    
    # Split into sentences
    sentences = []
    for sentence in text.split('.'):
        sentence = sentence.strip()
        if sentence and len(sentence) > 10:  # Filter very short sentences
            sentences.append(sentence + '.')
    
    if not sentences:
        # If no proper sentences, just truncate
        return text[:max_chars] + ('...' if len(text) > max_chars else '')
    
    # Take first few sentences that fit within max_chars
    summary_parts = []
    current_length = 0
    
    for sentence in sentences[:5]:  # Max 5 sentences
        if current_length + len(sentence) <= max_chars:
            summary_parts.append(sentence)
            current_length += len(sentence)
        else:
            break
    
    if not summary_parts:
        # If even first sentence is too long, truncate it
        return sentences[0][:max_chars] + ('...' if len(sentences[0]) > max_chars else '')
    
    return ' '.join(summary_parts)


def cleanup_summarizer():
    """Clean up the summarizer to free memory."""
    global _summarizer
    if _summarizer is not None:
        logger.info("Cleaning up summarizer")
        del _summarizer
        _summarizer = None
