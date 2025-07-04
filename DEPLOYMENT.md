# Deployment Guide

## Free Hosting Options

### 1. Render (Recommended - Easiest)

**Steps:**
1. Go to [render.com](https://render.com) and create an account
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `pokemon-pvp-analyzer` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click "Create Web Service"
6. Wait for deployment (2-3 minutes)

**URL**: `https://your-app-name.onrender.com`

### 2. Railway

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Python app
6. Add environment variable: `PORT=8000`

### 3. PythonAnywhere

**Steps:**
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Create free account
3. Go to "Web" tab → "Add a new web app"
4. Choose "Flask" and Python 3.9
5. Upload your files or clone from GitHub
6. Set up virtual environment and install requirements

## Important Notes

- **App Sleep**: Render free tier puts apps to sleep after 15 minutes of inactivity
- **First Load**: May take 10-30 seconds to wake up
- **Custom Domain**: All services support custom domains (you'd need to buy one)
- **HTTPS**: All services provide free SSL certificates

## Troubleshooting

If you get errors:
1. Check that `gunicorn` is in requirements.txt
2. Ensure `app:app` refers to your Flask app instance
3. Make sure all files are committed to GitHub
4. Check the deployment logs for specific errors

## Performance Tips

- The app will be slower on free tiers
- Consider caching frequently accessed data
- The PokeAPI calls might be slower on free hosting 