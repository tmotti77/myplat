# 🚀 Production Deployment Guide - MyPlat RAG Platform

**Deployment Stack:** Supabase + Railway + Vercel
**Time to Deploy:** 20-30 minutes
**Monthly Cost:** $32-40 (all services)
**Status:** Production-Ready

---

## 📋 Overview

We're deploying:
- **Frontend (Next.js)** → Vercel (FREE)
- **Backend (FastAPI)** → Railway ($7-15/month)
- **Database (PostgreSQL + pgvector)** → Supabase ($25/month)
- **Storage (Files/Documents)** → Supabase (included)
- **Redis (Caching)** → Upstash ($0-10/month)

**Total:** ~$32-50/month for production-grade infrastructure

---

## ✅ Prerequisites

- GitHub account
- Credit card (for paid services, won't charge until you upgrade)
- Your OpenAI API key (from https://platform.openai.com/api-keys)

---

## STEP 1: Set Up Supabase (Database + Storage)

### 1.1 Create Supabase Account

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub
4. Click "New Project"

### 1.2 Create Project

**Project Settings:**
- **Name:** `myplat-rag`
- **Database Password:** `RagSecureDB2024!` (save this!)
- **Region:** Choose closest to you (e.g., US East)
- **Plan:** Free (can upgrade later)

Click "Create new project" - takes ~2 minutes

### 1.3 Enable pgvector Extension

Once project is ready:

1. Go to **Database** → **Extensions** (left sidebar)
2. Search for "vector"
3. Enable **pgvector** (toggle switch)
4. Wait 10 seconds for activation

### 1.4 Get Connection String

1. Go to **Settings** → **Database** (left sidebar)
2. Scroll to **Connection String**
3. Select **URI** tab
4. Copy the connection string (looks like):
   ```
   postgresql://postgres:RagSecureDB2024!@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```

### 1.5 Create Storage Bucket

1. Go to **Storage** (left sidebar)
2. Click "Create a new bucket"
3. **Name:** `rag-documents`
4. **Public:** No (keep private)
5. Click "Create bucket"

**Save These Values:**
```
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (from Settings → API)
SUPABASE_DB_URL=postgresql://postgres:RagSecureDB2024!@db.xxxxx.supabase.co:5432/postgres
```

---

## STEP 2: Set Up Upstash Redis (Caching)

### 2.1 Create Upstash Account

1. Go to https://upstash.com
2. Sign up with GitHub
3. Click "Create Database"

### 2.2 Create Redis Database

**Settings:**
- **Name:** `myplat-cache`
- **Type:** Regional (cheaper) or Global (faster)
- **Region:** Same as Supabase
- **TLS:** Enabled

Click "Create"

### 2.3 Get Redis URL

1. Click on your database
2. Go to **Details** tab
3. Copy **REST URL** (looks like):
   ```
   https://us1-sharing-cod-12345.upstash.io
   ```

**Save These Values:**
```
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxx...
```

---

## STEP 3: Deploy Backend to Railway

### 3.1 Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Verify email

### 3.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select `tmotti77/myplat` repository
5. Railway will detect the project automatically

### 3.3 Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```bash
# Database (from Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:RagSecureDB2024!@db.xxxxx.supabase.co:5432/postgres

# Redis (from Upstash) - convert to redis:// format
REDIS_URL=redis://default:AXxxx@us1-sharing-cod-12345.upstash.io:6379

# OpenAI (use your actual key from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_OPENAI_KEY_HERE

# Security (from .env file)
JWT_SECRET_KEY=cadd8008fa2a9d879637cbf6e201e1030b6a146c1bec0aeef98504c8d0220f7b
SECRET_KEY=a4cba03185015cd66812728f37aaa113499dca96853ecaed7263c87c098f8602

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONPATH=/app

# CORS (will add frontend URL later)
CORS_ORIGINS=["https://yourdomain.vercel.app"]

# Storage (Supabase)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
MINIO_BUCKET_NAME=rag-documents
```

### 3.4 Deploy Backend

1. Railway will automatically deploy
2. Wait 2-5 minutes
3. Check **Deployments** tab - should show "Success"
4. Copy your backend URL: `https://myplat-production.up.railway.app`

### 3.5 Run Database Migrations

In Railway, go to **Settings** → **Deploy** → **Custom Start Command**:

**One-time migration (do this first):**
```bash
alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

After first deploy, change to:
```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

---

## STEP 4: Deploy Frontend to Vercel

### 4.1 Create Vercel Account

1. Go to https://vercel.com
2. Sign up with GitHub
3. Skip team creation

### 4.2 Import Project

1. Click "Add New..." → "Project"
2. Import `tmotti77/myplat` repository
3. Vercel will detect Next.js automatically

### 4.3 Configure Build Settings

**Root Directory:** `frontend`

**Environment Variables:**
```bash
NEXT_PUBLIC_API_URL=https://myplat-production.up.railway.app
```

### 4.4 Deploy Frontend

1. Click "Deploy"
2. Wait 2-3 minutes
3. Copy your frontend URL: `https://myplat.vercel.app`

### 4.5 Update Backend CORS

Go back to Railway → **Variables** → Update:
```bash
CORS_ORIGINS=["https://myplat.vercel.app","https://myplat-production.up.railway.app"]
```

Redeploy backend (Railway → **Deployments** → "Redeploy")

---

## STEP 5: Initialize Database

### 5.1 Run Migrations

Railway should have run migrations automatically. To verify:

1. Railway → **Deployments** → Click latest deployment
2. Check **Logs** - should see "Running migrations..."
3. If not, redeploy with migration command (Step 3.5)

### 5.2 Create Admin User (Optional)

In Railway → **Settings** → **Variables**, temporarily add:
```bash
CREATE_ADMIN_USER=true
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=SecurePassword123!
```

Redeploy, then remove these variables.

---

## STEP 6: Test Your Deployment

### 6.1 Test Backend

Open: `https://myplat-production.up.railway.app/docs`

You should see the FastAPI interactive docs with all 51 endpoints.

### 6.2 Test Frontend

Open: `https://myplat.vercel.app`

You should see the login page.

### 6.3 Test Full Workflow

1. **Create Account** → Sign up
2. **Upload Document** → Upload a PDF
3. **Search** → Search for content
4. **Chat** → Ask questions
5. **Verify AI Response** → Should get answers with citations

---

## 📊 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Vercel (Frontend) | Hobby | FREE |
| Railway (Backend) | Hobby | $5/month + usage (~$7-15) |
| Supabase (Database + Storage) | Pro | $25/month |
| Upstash (Redis) | Pay-as-you-go | ~$0-10/month |
| **TOTAL** | | **$32-50/month** |

**Free Tier Available:**
- Vercel: FREE forever for hobby projects
- Railway: $5 credit/month (enough for light testing)
- Supabase: FREE tier (500MB database, 1GB storage)
- Upstash: FREE tier (10k requests/day)

**Start with free tiers = $0/month for testing!**

---

## 🔧 Post-Deployment Configuration

### Update Custom Domain (Optional)

**Frontend (Vercel):**
1. Vercel → Project Settings → Domains
2. Add `yourdomain.com`
3. Update DNS records as shown

**Backend (Railway):**
1. Railway → Settings → Domains
2. Add `api.yourdomain.com`
3. Update DNS records

### Enable Monitoring

**Railway:**
1. Go to **Observability** tab
2. View metrics (CPU, Memory, Network)

**Supabase:**
1. Go to **Reports** tab
2. View database metrics

---

## 🐛 Troubleshooting

### Backend Not Starting

**Check Railway Logs:**
1. Railway → Deployments → Click deployment → Logs
2. Look for errors

**Common Issues:**
- Missing environment variables
- Database connection failed (check DATABASE_URL)
- Port binding (should use $PORT variable)

### Frontend Can't Connect to Backend

**Check:**
1. CORS settings in Railway (CORS_ORIGINS)
2. API URL in Vercel (NEXT_PUBLIC_API_URL)
3. Backend is actually running (test `/docs` endpoint)

### Database Migrations Failed

**Manual Migration:**
1. Railway → Settings → Variables → Add `RUN_MIGRATIONS=true`
2. Redeploy
3. Check logs for "Applied X migrations"

---

## 📈 Scaling for Production

### When you get 100+ users:

1. **Upgrade Supabase to Pro:** $25/month
   - 8GB database
   - 100GB storage
   - Daily backups

2. **Upgrade Railway:** $20-50/month
   - More CPU/RAM
   - Autoscaling

3. **Add Redis caching properly:**
   - Cache search results
   - Cache embeddings
   - Cache user sessions

4. **Add monitoring:**
   - Sentry for error tracking
   - LogRocket for user sessions
   - PostHog for analytics

---

## ✅ Deployment Checklist

- [ ] Supabase project created
- [ ] pgvector extension enabled
- [ ] Storage bucket created
- [ ] Upstash Redis created
- [ ] Railway backend deployed
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Vercel frontend deployed
- [ ] CORS configured correctly
- [ ] Backend `/docs` accessible
- [ ] Frontend loads
- [ ] Can create user account
- [ ] Can upload document
- [ ] Can search documents
- [ ] Can chat with AI
- [ ] AI returns responses with citations

---

## 🎉 Success Criteria

When everything is working:
- ✅ Backend responding at `https://yourapp.up.railway.app/docs`
- ✅ Frontend loading at `https://yourapp.vercel.app`
- ✅ Can sign up and log in
- ✅ Can upload PDF/DOCX documents
- ✅ Can search uploaded documents
- ✅ Can chat and get AI responses
- ✅ Responses include source citations
- ✅ All within 2 seconds response time

---

## 📞 Need Help?

**Railway Community:** https://discord.gg/railway
**Supabase Community:** https://discord.gg/supabase
**Vercel Community:** https://discord.gg/vercel

---

## 🔐 Security Notes

1. **Never commit .env files** (already in .gitignore)
2. **Rotate API keys every 90 days**
3. **Use strong database passwords**
4. **Enable 2FA on all services**
5. **Monitor unusual activity** in Railway/Supabase dashboards

---

**Your platform is now production-ready and deployed! 🚀**

Total setup time: 20-30 minutes
Monthly cost: $32-50 (or FREE with free tiers)
Ready to scale to thousands of users!
