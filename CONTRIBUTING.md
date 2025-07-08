# Contributing to Pokemon PvP Analyzer

Thank you for your interest in contributing to Pokemon PvP Analyzer! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch
4. **Make** your changes
5. **Test** your changes
6. **Submit** a pull request

## 📋 Development Setup

### Prerequisites
- Python 3.7 or higher
- Git
- A code editor (VS Code, PyCharm, etc.)

### Local Development
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pokemon-pvp-analyzer.git
cd pokemon-pvp-analyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions small and focused

### Security
- Always validate and sanitize user input
- Never expose sensitive information in error messages
- Follow the security guidelines in `SECURITY.md`
- Test for common vulnerabilities (XSS, CSRF, etc.)

### Testing
- Test your changes thoroughly
- Include unit tests for new functionality
- Test edge cases and error conditions
- Ensure the application works on different browsers

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, browser, Python version)
5. **Screenshots** if applicable

## 💡 Feature Requests

When suggesting features:

1. **Describe** the feature clearly
2. **Explain** why it would be useful
3. **Provide** examples of how it would work
4. **Consider** the impact on existing functionality

## 🔧 Pull Request Process

1. **Create** a descriptive branch name (e.g., `feature/add-new-move-type`)
2. **Make** focused, atomic commits
3. **Write** clear commit messages
4. **Test** your changes thoroughly
5. **Update** documentation if needed
6. **Submit** a pull request with a clear description

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security improvement

## Testing
- [ ] Tested locally
- [ ] Added unit tests
- [ ] Tested on multiple browsers

## Checklist
- [ ] Code follows style guidelines
- [ ] Security considerations addressed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🔒 Security

### Reporting Security Issues
**Do not** create public issues for security vulnerabilities. Instead:

1. Email the maintainer privately
2. Provide detailed reproduction steps
3. Allow reasonable time for fix
4. Coordinate disclosure timeline

### Security Guidelines
- Never commit sensitive data (API keys, passwords)
- Always validate user input
- Use parameterized queries
- Follow the principle of least privilege
- Keep dependencies updated

## 📚 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Focus on the code, not the person

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Pokemon PvP Analyzer! 🎉 