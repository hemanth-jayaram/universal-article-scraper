#!/usr/bin/env python3
"""
Setup script for Homepage Article Scraper
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read development requirements
def read_dev_requirements():
    try:
        with open("requirements-dev.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

setup(
    name="homepage-article-scraper",
    version="1.0.0",
    author="Homepage Article Scraper Team",
    author_email="contact@example.com",
    description="A high-performance web scraper for extracting articles from news websites and blogs with AI-powered summarization",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/homepage-article-scraper",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/homepage-article-scraper/issues",
        "Documentation": "https://github.com/yourusername/homepage-article-scraper#readme",
        "Source Code": "https://github.com/yourusername/homepage-article-scraper",
    },
    packages=find_packages(include=["scraper", "scraper.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": read_dev_requirements(),
        "test": [
            "pytest>=8.2.2",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.3.1",
            "pytest-mock>=3.11.1",
            "pytest-asyncio>=0.21.1",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "homepage-scraper=run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml"],
    },
    keywords=[
        "web-scraping",
        "content-extraction", 
        "ai-summarization",
        "news",
        "blog",
        "scrapy",
        "nlp",
        "bert",
        "bart",
        "transformers",
    ],
    zip_safe=False,
)
