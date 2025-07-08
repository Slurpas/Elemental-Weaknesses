# Deployment Guide for Pokemon PvP Helper

## Prerequisites

Before deploying, make sure you have:
1. **Environment variables configured** (see [ENVIRONMENT.md](ENVIRONMENT.md))
2. **All files committed** to your GitHub repository
3. **No sensitive data** in your code (use environment variables)

## Free Hosting Options

### 1. Render (Recommended - Easiest)

**Steps:**
1. Go to [render.com](https://render.com) and create an account
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `pokemon-pvp-helper` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **Set Environment Variables** (in the Environment tab):
   - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `False`
   - `ANALYTICS_PASSWORD`: Choose a strong password
6. Click "Create Web Service"
7. Wait for deployment (2-3 minutes)

**URL**: `https://your-app-name.onrender.com`

### 2. Railway

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Python app
6. **Add Environment Variables** (in Variables tab):
   - `SECRET_KEY`: Your secure secret key
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `False`
   - `ANALYTICS_PASSWORD`: Your analytics password
   - `PORT`: `8000`

### 3. PythonAnywhere

**Steps:**
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Create free account
3. Go to "Web" tab → "Add a new web app"
4. Choose "Flask" and Python 3.9
5. Upload your files or clone from GitHub
6. Set up virtual environment and install requirements
7. **Configure Environment Variables** (in Web app settings):
   - Add each required environment variable

## Security Checklist

Before going live, ensure:

- ✅ **No secrets in code**: All sensitive data uses environment variables
- ✅ **Analytics data protected**: `analytics_data.json` is gitignored
- ✅ **Strong passwords**: Analytics dashboard has a secure password
- ✅ **HTTPS enabled**: All hosting providers offer free SSL
- ✅ **Debug mode off**: `FLASK_DEBUG=False` in production

## Environment Variables

**Required for all deployments:**
```bash
SECRET_KEY=your-secure-secret-key
FLASK_ENV=production
FLASK_DEBUG=False
ANALYTICS_PASSWORD=your-analytics-password
```

**Optional:**
```bash
PORT=5000  # Custom port (if needed)
```

See [ENVIRONMENT.md](ENVIRONMENT.md) for detailed setup instructions.

## Important Notes

- **App Sleep**: Render free tier puts apps to sleep after 15 minutes of inactivity
- **First Load**: May take 10-30 seconds to wake up
- **Custom Domain**: All services support custom domains (you'd need to buy one)
- **HTTPS**: All services provide free SSL certificates
- **Analytics**: Data is stored locally and not shared with third parties

## Troubleshooting

### Common Issues

1. **"SECRET_KEY not set" error**:
   - Check environment variables are set correctly
   - Verify variable names match exactly

2. **Analytics dashboard not working**:
   - Ensure `ANALYTICS_PASSWORD` is set
   - Check password matches what you're entering

3. **App crashes on startup**:
   - Check deployment logs for specific errors
   - Verify all required environment variables are set
   - Ensure `gunicorn` is in requirements.txt

4. **Build fails**:
   - Check that `python-dotenv` is in requirements.txt
   - Verify all files are committed to GitHub
   - Check build logs for specific error messages

### Performance Tips

- The app will be slower on free tiers
- Consider caching frequently accessed data
- The PvPoke data calls might be slower on free hosting
- Analytics data is stored locally and won't affect performance

## Post-Deployment

After successful deployment:

1. **Test all features**:
   - Pokemon search
   - Team building
   - Battle simulation
   - Analytics dashboard (with password)

2. **Monitor logs** for any errors

3. **Update documentation** with your live URL

4. **Share with community** (if desired)

## Support

If you encounter issues:
1. Check this guide and [ENVIRONMENT.md](ENVIRONMENT.md)
2. Review deployment logs
3. Verify environment variables are set correctly
4. Contact the project maintainers if problems persist 