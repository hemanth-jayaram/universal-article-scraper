# Contributing to Homepage Article Scraper

Thank you for your interest in contributing to the Homepage Article Scraper! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker to report bugs or request features
- Include detailed information about your environment and the issue
- Provide steps to reproduce the problem
- Include relevant error messages and logs

### Suggesting Features
- Open a new issue with the "enhancement" label
- Describe the feature and its benefits
- Consider implementation complexity and maintenance burden

### Code Contributions
- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Make your changes
- Add tests for new functionality
- Ensure all tests pass
- Submit a pull request

## 🏗️ Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- pip or conda

### Local Development
```bash
# Clone the repository
git clone https://github.com/yourusername/homepage-article-scraper.git
cd homepage-article-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install pre-commit hooks
pre-commit install
```

### Development Dependencies
```bash
# Install development tools
pip install pytest pytest-cov black isort flake8 mypy pre-commit
```

## 📝 Code Style

### Python Style Guide
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for function parameters and return values
- Keep functions focused and under 50 lines when possible
- Use descriptive variable and function names

### Code Formatting
We use automated tools to maintain consistent code style:

```bash
# Format code with Black
black scraper/ tests/

# Sort imports with isort
isort scraper/ tests/

# Check code style with flake8
flake8 scraper/ tests/

# Type checking with mypy
mypy scraper/
```

### Pre-commit Hooks
The project uses pre-commit hooks to automatically format and check code:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraper

# Run specific test file
pytest tests/test_extractors.py

# Run tests in parallel
pytest -n auto
```

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies when appropriate
- Aim for >90% code coverage

### Test Structure
```
tests/
├── test_extractors.py      # Test content extraction
├── test_link_filters.py    # Test link filtering
├── test_summarizer.py      # Test AI summarization
├── test_spiders.py         # Test spider functionality
└── conftest.py            # Test configuration and fixtures
```

## 🔧 Development Workflow

### Branch Naming
- `feature/feature-name` - New features
- `bugfix/issue-description` - Bug fixes
- `docs/documentation-update` - Documentation changes
- `refactor/component-name` - Code refactoring

### Commit Messages
Use conventional commit format:
```
type(scope): description

feat(extractors): add support for new content type
fix(spider): resolve memory leak in article processing
docs(readme): update installation instructions
refactor(summarizer): optimize model loading
```

### Pull Request Process
1. Ensure your branch is up to date with main
2. Write clear commit messages
3. Include tests for new functionality
4. Update documentation if needed
5. Request review from maintainers
6. Address feedback and suggestions

## 📚 Documentation

### Code Documentation
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Include examples for complex functions
- Document exceptions and edge cases

### Project Documentation
- Keep README.md up to date
- Update PROJECT_DOCUMENTATION.md for major changes
- Include code examples in documentation
- Document configuration options

## 🚀 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes, backward compatible

### Release Checklist
- [ ] Update version in `__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release tag
- [ ] Publish to PyPI (if applicable)

## 🐛 Bug Reports

### Required Information
- Python version
- Operating system
- Scrapy version
- Error messages and stack traces
- Steps to reproduce
- Expected vs actual behavior

### Example Bug Report
```markdown
**Bug Description**
Brief description of the issue

**Steps to Reproduce**
1. Run command: `python run.py "https://example.com"`
2. Observe error: [paste error message]

**Environment**
- OS: Ubuntu 20.04
- Python: 3.11.0
- Scrapy: 2.13.3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens
```

## 💡 Feature Requests

### Guidelines
- Explain the problem you're trying to solve
- Describe your proposed solution
- Consider alternative approaches
- Discuss implementation complexity
- Provide use case examples

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on technical merit
- Welcome newcomers
- Provide constructive feedback
- Follow the project's coding standards

### Communication
- Use GitHub issues for technical discussions
- Be clear and concise in communications
- Ask questions when unsure
- Help others when possible

## 📞 Getting Help

### Resources
- [Project Documentation](PROJECT_DOCUMENTATION.md)
- [GitHub Issues](https://github.com/yourusername/homepage-article-scraper/issues)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Python Documentation](https://docs.python.org/)

### Questions
- Search existing issues first
- Ask in GitHub discussions
- Provide context and error details
- Be patient for responses

## 🙏 Acknowledgments

Thank you to all contributors who have helped improve this project. Your contributions make the Homepage Article Scraper better for everyone!

---

*This contributing guide is a living document. Feel free to suggest improvements or ask questions about any part of the contribution process.*
