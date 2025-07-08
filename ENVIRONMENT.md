# Environment Variables Guide

This document explains all environment variables used by Pokemon PvP Helper and how to configure them for different environments.

## Required Environment Variables

### For Production Deployment

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

# Analytics Dashboard
ANALYTICS_PASSWORD=your-analytics-password-here

# Optional: Custom Port (default: 5000)
PORT=5000
```

### For Development

```bash
# Flask Configuration
SECRET_KEY=dev-secret-key-123
FLASK_ENV=development
FLASK_DEBUG=True

# Analytics Dashboard
ANALYTICS_PASSWORD=dev-password

# Optional: Custom Port
PORT=5000
```

## How to Set Environment Variables

### Local Development

1. **Create a `.env` file** in your project root:
   ```bash
   # .env file
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   FLASK_DEBUG=True
   ANALYTICS_PASSWORD=your-analytics-password
   ```

2. **Install python-dotenv** (add to requirements.txt):
   ```bash
   pip install python-dotenv
   ```

3. **Load the .env file** in your app.py:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Production Deployment

#### Render
1. Go to your app dashboard
2. Click "Environment" tab
3. Add each variable:
   - `SECRET_KEY`: Generate a secure random string
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `False`
   - `ANALYTICS_PASSWORD`: Choose a strong password

#### Railway
1. Go to your project dashboard
2. Click "Variables" tab
3. Add each environment variable

#### PythonAnywhere
1. Go to "Web" tab
2. Click on your web app
3. Go to "Environment variables" section
4. Add each variable

## Security Best Practices

### SECRET_KEY
- **Generate a secure key**: Use `python -c "import secrets; print(secrets.token_hex(32))"`
- **Never commit to git**: Always use environment variables
- **Use different keys**: Different keys for development and production

### ANALYTICS_PASSWORD
- **Choose a strong password**: At least 12 characters, mix of letters, numbers, symbols
- **Keep it private**: Only share with trusted team members
- **Change regularly**: Update periodically for security

### FLASK_DEBUG
- **Development**: `True` (shows detailed error pages)
- **Production**: `False` (hides sensitive information)

## Example .env File

```bash
# Development Environment
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True
ANALYTICS_PASSWORD=dev-analytics-password
PORT=5000

# Production Environment (example)
# SECRET_KEY=your-actual-production-secret-key
# FLASK_ENV=production
# FLASK_DEBUG=False
# ANALYTICS_PASSWORD=your-actual-production-password
# PORT=5000
```

## Troubleshooting

### Common Issues

1. **"SECRET_KEY not set" error**:
   - Make sure `.env` file exists and is in the project root
   - Check that `python-dotenv` is installed
   - Verify the variable name is exactly `SECRET_KEY`

2. **Analytics dashboard not working**:
   - Ensure `ANALYTICS_PASSWORD` is set
   - Check that the password matches what you're entering

3. **App crashes on startup**:
   - Verify all required environment variables are set
   - Check for typos in variable names
   - Ensure `.env` file is not committed to git

### Validation

You can test your environment variables by running:
```python
import os
print(f"SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'Not set')}")
print(f"ANALYTICS_PASSWORD: {'Set' if os.getenv('ANALYTICS_PASSWORD') else 'Not set'}")
```

## Privacy and Analytics

- **Analytics data is stored locally** in `analytics_data.json`
- **This file is gitignored** and will not be uploaded to GitHub
- **No personal data is collected** - only anonymous usage statistics
- **IP addresses are hashed** for privacy protection
- **Analytics dashboard is password-protected** for admin access only

## Support

If you need help with environment variables:
1. Check this guide first
2. Review the deployment logs
3. Ensure all required variables are set
4. Contact the project maintainers if issues persist 