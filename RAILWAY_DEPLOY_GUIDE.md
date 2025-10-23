# 🚂 Railway Backend Deployment - Step by Step

**Time:** 5-7 minutes
**Cost:** $7-15/month (or use $5 free credit for testing)

---

## 🎯 STEP 1: Create Railway Account

1. Go to: https://railway.app
2. Click "Login" (top right)
3. Click "Login with GitHub"
4. Authorize Railway

---

## 🎯 STEP 2: Create New Project

1. Click **"New Project"** (big button)
2. Select **"Deploy from GitHub repo"**
3. If asked, click **"Configure GitHub App"**
4. Select **"Only select repositories"**
5. Choose **"tmotti77/myplat"**
6. Click **"Install & Authorize"**
7. Back in Railway, select **"tmotti77/myplat"** repository

---

## 🎯 STEP 3: Configure the Deployment

Railway will auto-detect your project. Now configure it:

1. **Root Directory:** Leave as default (root)
2. **Build Command:** Railway will auto-detect
3. Click on the service that was created

---

## 🎯 STEP 4: Add Environment Variables

This is the MOST IMPORTANT step!

1. Click **"Variables"** tab (in your service)
2. Click **"+ New Variable"** or **"Raw Editor"** button
3. **Copy and paste ALL of these:**

```bash
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:RagSecureDB2024!@db.wkhcilgrqudlducevyud.supabase.co:5432/postgres

# Redis (Upstash)
REDIS_URL=redis://default:AW6AAAIncDJmMTAwZDhjMmIzYTM0YWQ4Yjk5ODhiNDNmOTQ5YzgxYnAyMjgyODg@absolute-rattler-28288.upstash.io:6379

# OpenAI (copy from DEPLOYMENT_CREDENTIALS.md - local file)
OPENAI_API_KEY=YOUR_OPENAI_KEY_FROM_DEPLOYMENT_CREDENTIALS_FILE

# Security Keys
JWT_SECRET_KEY=cadd8008fa2a9d879637cbf6e201e1030b6a146c1bec0aeef98504c8d0220f7b
SECRET_KEY=a4cba03185015cd66812728f37aaa113499dca96853ecaed7263c87c098f8602
ENCRYPTION_KEY=73208082c5f30fe605b69bc0a1664c25

# Supabase API
SUPABASE_URL=https://wkhcilgrqudlducevyud.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndraGNpbGdycXVkbGR1Y2V2eXVkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMjM0MDAsImV4cCI6MjA3Njc5OTQwMH0.rvaqNJqUR7kH2gO4Id2PnG264tDBCYKpWCACWiU76pY
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndraGNpbGdycXVkbGR1Y2V2eXVkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTIyMzQwMCwiZXhwIjoyMDc2Nzk5NDAwfQ.0jcohO4epPH_sE2KnRcdkIEpYU-IxTpEyMqKtkKUvKg

# Storage
MINIO_BUCKET_NAME=rag-documents

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONPATH=/app

# CORS (will update with Vercel URL later)
CORS_ORIGINS=["*"]

# AI Models
EMBEDDING_MODEL=text-embedding-3-large
DEFAULT_LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.1
MAX_TOKENS=4000

# Feature Flags
ENABLE_REAL_TIME_UPDATES=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_EXPERT_SYSTEM=true
ENABLE_FEEDBACK_LEARNING=true
```

4. Click **"Save"** or click outside the editor

---

## 🎯 STEP 5: Deploy!

1. Railway will automatically start deploying
2. Click **"Deployments"** tab to watch progress
3. Wait 2-5 minutes for build to complete
4. Look for **"Success ✓"** message

---

## 🎯 STEP 6: Get Your Backend URL

1. Click **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"**
4. Railway will create a URL like: `https://myplat-production.up.railway.app`
5. **COPY THIS URL** - you'll need it for Vercel!

---

## 🎯 STEP 7: Run Database Migrations

1. Still in **"Settings"** tab
2. Scroll to **"Deploy"** section
3. Find **"Custom Start Command"**
4. Add this command:
   ```bash
   alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
5. Click **"Save"**
6. Go to **"Deployments"** tab
7. Click **"Redeploy"** (top right)
8. Wait for deployment to finish

**After first successful deployment**, change the start command to:
```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```
(Remove the `alembic upgrade head &&` part - migrations only need to run once)

---

## ✅ STEP 8: Test Your Backend

1. Copy your Railway URL (from Step 6)
2. Add `/docs` to the end
3. Open in browser: `https://your-app.up.railway.app/docs`
4. **You should see:** FastAPI interactive documentation with 51 endpoints!

---

## 🎉 SUCCESS!

Your backend is now live!

**Save your Railway URL:**
```
Backend URL: https://your-app.up.railway.app
```

You'll need this URL for the Vercel frontend deployment!

---

## 🐛 Troubleshooting

**Build Failed?**
- Check **"Deployments"** → Click failed deployment → View logs
- Common issue: Missing Python packages
- Solution: Railway should auto-detect and install from `pyproject.toml`

**Can't access /docs?**
- Check deployment is "Success" not "Building"
- Check domain is generated in Settings
- Try adding `/health` endpoint first

**Database connection error?**
- Verify DATABASE_URL is correct in Variables
- Make sure it starts with `postgresql+asyncpg://`
- Check Supabase project is not paused

---

**Next:** Deploy your frontend to Vercel! Check `VERCEL_DEPLOY_GUIDE.md`
