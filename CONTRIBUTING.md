# 🤝 Contributing to AI Agent Web Generator

Thank you for your interest in contributing to AI Agent Web Generator! We welcome contributions from the community and appreciate your help in making this project better.

## 🎯 How to Contribute

### 🐛 Reporting Bugs
- Use the [GitHub Issues](https://github.com/yourusername/ai-agent-web-generator/issues) page
- Include a clear description of the bug
- Provide steps to reproduce the issue
- Include error messages and logs if applicable
- Mention your operating system and Python version

### 💡 Suggesting Features
- Use the [GitHub Issues](https://github.com/yourusername/ai-agent-web-generator/issues) page
- Describe the feature you'd like to see
- Explain why this feature would be useful
- Provide examples of how it would work

### 🔧 Code Contributions

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/ai-agent-web-generator.git
   cd ai-agent-web-generator
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Set up your development environment**
   ```bash
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Make your changes**
   - Follow the existing code style
   - Add tests for new features
   - Update documentation if needed

5. **Test your changes**
   ```bash
   python start.py  # Test locally
   python start_simple.py  # Test with Cloudflare
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m 'Add amazing feature'
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

8. **Create a Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template

## 📋 Pull Request Guidelines

### Before submitting a PR:
- [ ] Code follows the existing style
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No new warnings or errors
- [ ] Feature works with both local and Cloudflare deployment

### PR Template:
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Tested locally
- [ ] Tested with Cloudflare deployment
- [ ] Added new tests

## Screenshots (if applicable)
Add screenshots of UI changes

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have made corresponding changes to documentation
```

## 🏗️ Development Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Cloudflare tunnel daemon (for testing global deployment)

### Local Development
```bash
# Clone and setup
git clone https://github.com/yourusername/ai-agent-web-generator.git
cd ai-agent-web-generator
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your OpenAI API key

# Run locally
python start.py
```

### Testing Global Deployment
```bash
# Test Cloudflare integration
python start_simple.py
```

## 📁 Project Structure

```
AI-Agent/
├── app/                    # Streamlit frontend
│   ├── main.py            # Main application
│   ├── components/        # UI components
│   └── utils/             # Utilities
├── api/                   # FastAPI backend
│   ├── main.py           # API server
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   └── utils/            # Utilities
├── tools/                 # Utility scripts
├── .cloudflare/          # Cloudflare config
└── [configuration files]
```

## 🎨 Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

### JavaScript/TypeScript
- Use modern ES6+ syntax
- Follow consistent naming conventions
- Add JSDoc comments for functions

### General
- Use meaningful variable and function names
- Keep code DRY (Don't Repeat Yourself)
- Add comments for complex logic
- Write self-documenting code

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_ai_service.py

# Run with coverage
python -m pytest --cov=app --cov=api
```

### Test Guidelines
- Write tests for new features
- Ensure tests pass before submitting PR
- Use descriptive test names
- Mock external dependencies

## 📚 Documentation

### Updating Documentation
- Update README.md for new features
- Add docstrings to new functions
- Update API documentation if endpoints change
- Include examples for new features

### Documentation Standards
- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Keep documentation up to date

## 🚀 Deployment Testing

### Local Testing
```bash
python start.py
# Access at http://localhost:8501
```

### Global Deployment Testing
```bash
python start_simple.py
# Check Cloudflare tunnel URLs
```

## 🤝 Community Guidelines

### Be Respectful
- Be kind and respectful to other contributors
- Use inclusive language
- Welcome newcomers and help them get started

### Communication
- Use clear, descriptive commit messages
- Respond to issues and PRs promptly
- Ask questions if something is unclear

### Quality
- Review your own code before submitting
- Test thoroughly
- Consider edge cases
- Think about user experience

## 🏆 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Project README (for significant contributions)
- Release notes

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the README and code comments

## 🎉 Thank You!

Thank you for contributing to AI Agent Web Generator! Your contributions help make this project better for everyone in the community.

---

**Happy coding! 🚀**
