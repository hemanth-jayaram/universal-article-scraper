#!/usr/bin/env python3
"""
Project verification script for Homepage Article Scraper.
Checks that all required files exist and can be imported.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (MISSING)")
        return False


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} (IMPORT ERROR: {e})")
        return False


def main():
    """Run project verification."""
    print("🔍 Homepage Article Scraper - Project Verification")
    print("=" * 60)
    
    all_good = True
    
    # Check core files
    print("\n📁 Core Files:")
    core_files = [
        ("README.md", "Documentation"),
        ("requirements.txt", "Dependencies"),
        ("run.py", "CLI Entry Point"),
    ]
    
    for filepath, desc in core_files:
        all_good &= check_file_exists(filepath, desc)
    
    # Check scraper package
    print("\n🕷️ Scraper Package:")
    scraper_files = [
        ("scraper/__init__.py", "Package Init"),
        ("scraper/settings.py", "Scrapy Settings"),
        ("scraper/link_filters.py", "Link Filters"),
        ("scraper/extractors.py", "Content Extractors"),
        ("scraper/summarizer.py", "Text Summarizer"),
        ("scraper/save.py", "File Utilities"),
        ("scraper/spiders/__init__.py", "Spiders Package"),
        ("scraper/spiders/homepage_spider.py", "Homepage Spider"),
    ]
    
    for filepath, desc in scraper_files:
        all_good &= check_file_exists(filepath, desc)
    
    # Check FastAPI app
    print("\n🌐 FastAPI Application:")
    app_files = [
        ("app/__init__.py", "App Package"),
        ("app/main.py", "FastAPI Main"),
        ("app/templates/index.html", "Web Template"),
    ]
    
    for filepath, desc in app_files:
        all_good &= check_file_exists(filepath, desc)
    
    # Check scripts
    print("\n📜 Helper Scripts:")
    script_files = [
        ("scripts/run_local.sh", "Local Runner (Bash)"),
        ("scripts/run_remote.ps1", "Remote Runner (PowerShell)"),
    ]
    
    for filepath, desc in script_files:
        all_good &= check_file_exists(filepath, desc)
    
    # Check tests
    print("\n🧪 Test Suite:")
    test_files = [
        ("tests/__init__.py", "Test Package"),
        ("tests/test_link_filters.py", "Link Filter Tests"),
        ("tests/test_save.py", "Save Utility Tests"),
        ("tests/run_tests.py", "Test Runner"),
    ]
    
    for filepath, desc in test_files:
        all_good &= check_file_exists(filepath, desc)
    
    # Check imports (if packages are installed)
    print("\n📦 Import Verification:")
    
    # Add current directory to path for testing
    sys.path.insert(0, '.')
    
    core_imports = [
        ("scraper.settings", "Scrapy Settings"),
        ("scraper.link_filters", "Link Filters"),
        ("scraper.extractors", "Content Extractors"),
        ("scraper.save", "File Utilities"),
        ("scraper.spiders.homepage_spider", "Homepage Spider"),
        ("app.main", "FastAPI App"),
    ]
    
    for module, desc in core_imports:
        all_good &= check_import(module, desc)
    
    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("🎉 PROJECT VERIFICATION PASSED!")
        print("\nThe Homepage Article Scraper is ready to use!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run CLI: python run.py \"https://www.bbc.com/news\"")
        print("3. Run web UI: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("4. Run tests: python tests/run_tests.py")
    else:
        print("❌ PROJECT VERIFICATION FAILED!")
        print("\nSome files are missing or have import errors.")
        print("Please check the output above for details.")
    
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
