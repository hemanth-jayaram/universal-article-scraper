---
name: Bug Report
about: Create a report to help us improve the scraper
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
1. Run command: `python run.py "https://example.com"`
2. Observe error: [paste error message here]
3. [Add more steps if needed]

## ✅ Expected Behavior
What you expected to happen.

## ❌ Actual Behavior
What actually happened.

## 🖥️ Environment
- **Operating System**: [e.g., Windows 10, Ubuntu 20.04, macOS 12.0]
- **Python Version**: [e.g., 3.11.0]
- **Scrapy Version**: [e.g., 2.13.3]
- **Scraper Version**: [e.g., 1.0.0]

## 📋 Additional Context
- **Target Website**: [e.g., https://www.bbc.com/news]
- **Error Messages**: [Paste full error messages and stack traces]
- **Logs**: [Attach relevant log files if available]
- **Screenshots**: [If applicable, add screenshots]

## 🔧 Configuration
```bash
# Environment variables (if any)
export CONCURRENT_REQUESTS=32
export MAX_ARTICLES=40
export SUMMARY_ENABLED=true
```

## 💡 Possible Solutions
If you have any ideas about what might be causing this or how to fix it, please share them.

## 📁 Files to Check
- [ ] `scraper/settings.py`
- [ ] `scraper/extractors.py`
- [ ] `scraper/spiders/homepage_spider.py`
- [ ] `requirements.txt`

## 🔍 Debug Information
```bash
# Run with verbose logging
python run.py "https://example.com" --verbose

# Check individual components
python -c "from scraper.extractors import extract_article; print('Extractors OK')"
python -c "from scraper.summarizer import get_summarizer; print('Summarizer OK')"
```

## 📝 Additional Notes
Any other context about the problem here.

---

**Thank you for reporting this issue!** We'll investigate and get back to you as soon as possible.
