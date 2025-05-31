# Contributing to Science Live Pipeline

Thank you for your interest in contributing to Science Live! We welcome contributions from researchers, developers, and anyone passionate about breaking down knowledge silos in science.

## 🚀 Quick Start for Contributors

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/science-live-pipeline.git
cd science-live-pipeline

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/
```

### Make Your First Contribution

1. **Find an issue** or propose a new feature
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** and add tests
4. **Run tests**: `pytest tests/`
5. **Submit a pull request**

## 🎯 Ways to Contribute

### For Researchers
- **Test with your domain**: Try Science Live with your research questions
- **Report issues**: Let us know what doesn't work or could be improved
- **Suggest nanopub sources**: Help us connect to relevant scientific databases
- **Domain expertise**: Help improve entity extraction for your field

### For Developers
- **Fix bugs**: Check our [GitHub Issues](https://github.com/ScienceLiveHub/science-live-pipeline/issues)
- **Add features**: Implement new pipeline steps or improve existing ones
- **Improve performance**: Optimize queries, caching, or processing speed
- **Enhance documentation**: Help other developers understand the codebase

### For Data Scientists
- **Improve NLP**: Enhance question processing and entity extraction
- **Better algorithms**: Improve confidence scoring and result ranking
- **Evaluation metrics**: Help us measure and improve pipeline effectiveness

## 📋 Contribution Guidelines

### Code Standards
- Follow existing code style (we use `black` for formatting)
- Add type hints where possible
- Write docstrings for new functions and classes
- Include tests for new functionality

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/ -m unit
pytest tests/ -m integration

# Check test coverage
pytest tests/ --cov=science_live
```

### Documentation
- Update docstrings for any changed functions
- Add examples for new features
- Update the quickstart guide if needed

## 🐛 Reporting Issues

When reporting bugs, please include:

- **Science Live version**: `pip show science-live`
- **Python version**: `python --version`
- **Operating system**
- **Question you asked** (if relevant)
- **Expected vs actual behavior**
- **Error messages** (full traceback if possible)

### Example Bug Report
```
**Bug**: Pipeline crashes with ORCID queries

**Environment**: 
- Science Live: 0.0.1
- Python: 3.9.2
- macOS 12.1

**Question**: "What papers by 0000-0002-1784-2920?"

**Error**: 
```
KeyError: 'author'
  at science_live/pipeline/entity_extractor.py:45
```

**Expected**: Should return author's publications
```

## 💡 Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** your feature would solve
3. **Provide use cases** from your research experience
4. **Suggest implementation** if you have ideas

### Example Feature Request
```
**Feature**: Support for chemical formula queries

**Problem**: Researchers can't easily find papers mentioning specific chemical compounds

**Use Case**: "What papers discuss H2SO4?" should find chemistry papers

**Implementation Ideas**: Add chemical formula regex patterns to entity extraction
```

## 🔧 Development Workflow

### Setting Up Your Environment
```bash
# Create development branch
git checkout -b feature/my-feature

# Make changes and test
# ... edit files ...
pytest tests/

# Commit with clear message
git commit -m "Add: Chemical formula entity extraction

- Recognize common chemical formulas (H2O, CO2, etc.)
- Add tests for chemistry domain queries
- Update documentation with chemistry examples"
```

### Pull Request Process
1. **Keep PRs focused**: One feature or fix per PR
2. **Write clear titles**: "Fix: ORCID entity linking error"
3. **Describe changes**: What you changed and why
4. **Link related issues**: "Fixes #123"
5. **Request reviews**: Tag relevant maintainers

## 🤝 Community Guidelines

- **Be respectful**: We're all here to advance science
- **Ask questions**: No question is too basic
- **Share knowledge**: Help others learn from your expertise
- **Credit others**: Acknowledge contributions and prior work

## 📞 Getting Help

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Check our [docs](https://sciencelivehub.github.io/science-live-pipeline)

## 🎉 Recognition

Contributors will be:
- Recognized in our README using the [All Contributors](https://allcontributors.org/) specification
- Acknowledged in release notes for their specific contributions
- Invited to co-author papers about Science Live (for significant contributions)
- Featured on GitHub's automatic contributors page

---

**Ready to contribute?** Check out our [good first issues](https://github.com/ScienceLiveHub/science-live-pipeline/labels/good%20first%20issue) or start by testing Science Live with your research questions!
