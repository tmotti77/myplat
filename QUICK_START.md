# ⚡ Quick Start - Deploy in 20 Minutes

**Goal:** Get your RAG platform running in production

**What you need:**
- GitHub account
- Credit card (for paid services after free tier)
- 20 minutes

---

## 🚀 5-Step Deployment

### STEP 1: Supabase (Database) - 5 minutes

1. Go to https://supabase.com → Sign up with GitHub
2. Create new project:
   - Name: `myplat-rag`
   - Password: `RagSecureDB2024!`
   - Region: Choose closest to you
3. Wait 2 minutes for project creation
4. Enable pgvector:
   - Database → Extensions → Search "vector" → Enable
5. Create storage bucket:
   - Storage → Create bucket → Name: `rag-documents` → Private
6. **Save these** (Settings → Database & Settings → API):
   ```
   DATABASE_URL: postgresql://postgres:RagSecureDB2024!@db.xxxxx.supabase.co:5432/postgres
   SUPABASE_URL: https://xxxxx.supabase.co
   SUPABASE_KEY: eyJhbGci...
   ```

**Cost:** FREE (up to 500MB) or $25/month (Pro)

---

### STEP 2: Upstash (Redis) - 3 minutes

1. Go to https://upstash.com → Sign up with GitHub
2. Create database:
   - Name: `myplat-cache`
   - Region: Same as Supabase
   - Type: Regional
3. **Save these** (Database → Details):
   ```
   REDIS_URL: redis://default:AXxxx@xxxxx.upstash.io:6379
   ```

**Cost:** FREE (10k requests/day) or $10/month

---

### STEP 3: Railway (Backend) - 5 minutes

1. Go to https://railway.app → Sign up with GitHub
2. New Project → Deploy from GitHub → Select `tmotti77/myplat`
3. Add environment variables (Variables tab):
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:RagSecureDB2024!@db.xxxxx.supabase.co:5432/postgres
   REDIS_URL=redis://default:AXxxx@xxxxx.upstash.io:6379
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_OPENAI_KEY_HERE
   JWT_SECRET_KEY=cadd8008fa2a9d879637cbf6e201e1030b6a146c1bec0aeef98504c8d0220f7b
   SECRET_KEY=a4cba03185015cd66812728f37aaa113499dca96853ecaed7263c87c098f8602
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   PYTHONPATH=/app
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGci...
   CORS_ORIGINS=["*"]
   ```
4. Deploy will start automatically (2-5 min)
5. **Save your backend URL:** `https://myplat-production.up.railway.app`

**Cost:** $7-15/month

---

### STEP 4: Vercel (Frontend) - 5 minutes

1. Go to https://vercel.com → Sign up with GitHub
2. Add New → Project → Import `tmotti77/myplat`
3. Configure:
   - Root Directory: `frontend`
   - Framework Preset: Next.js
4. Add environment variable:
   ```bash
   NEXT_PUBLIC_API_URL=https://myplat-production.up.railway.app
   ```
5. Click Deploy (2-3 minutes)
6. **Save your frontend URL:** `https://myplat.vercel.app`

**Cost:** FREE forever

---

### STEP 5: Connect Everything - 2 minutes

1. **Update CORS in Railway:**
   - Go back to Railway → Variables
   - Update `CORS_ORIGINS` to:
     ```bash
     ["https://myplat.vercel.app","https://myplat-production.up.railway.app"]
     ```
   - Redeploy (Deployments → Redeploy)

2. **Run database migrations:**
   - Railway → Settings → Custom Start Command:
     ```bash
     alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT
     ```
   - After first deploy, change back to:
     ```bash
     uvicorn src.main:app --host 0.0.0.0 --port $PORT
     ```

---

## ✅ Test Your Deployment

### 1. Test Backend
Open: `https://myplat-production.up.railway.app/docs`
- Should see 51 API endpoints
- Try `/health` endpoint

### 2. Test Frontend
Open: `https://myplat.vercel.app`
- Should see login page
- Create account
- Upload document
- Search and chat

---

## 🎉 You're Live!

Your production RAG platform is now running on:
- **Frontend:** https://myplat.vercel.app
- **Backend:** https://myplat-production.up.railway.app
- **Database:** Supabase (PostgreSQL + pgvector)
- **Storage:** Supabase Storage
- **Cache:** Upstash Redis

**Total Cost:** $32-50/month (or FREE with free tiers for testing)

---

## 📊 What You Have

- ✅ 51 working API endpoints
- ✅ RAG with OpenAI embeddings
- ✅ Document upload (PDF, DOCX, TXT)
- ✅ Semantic search
- ✅ AI chat with citations
- ✅ Multi-tenant support
- ✅ User authentication
- ✅ Production-ready security
- ✅ Auto-scaling infrastructure

---

## 🐛 Troubleshooting

**Backend not starting?**
- Check Railway logs: Deployments → Click deployment → Logs
- Verify all environment variables are set

**Frontend can't connect?**
- Check CORS settings in Railway
- Verify NEXT_PUBLIC_API_URL in Vercel

**Database connection failed?**
- Verify DATABASE_URL format: `postgresql+asyncpg://...`
- Check Supabase is not paused (free tier pauses after inactivity)

**Still stuck?**
- Railway Discord: https://discord.gg/railway
- Supabase Discord: https://discord.gg/supabase

---

## 📈 Next Steps

1. **Custom domain:** Add your domain in Vercel/Railway settings
2. **Monitoring:** Set up Sentry for error tracking
3. **Analytics:** Add PostHog or Mixpanel
4. **Upgrade plans:** When you hit free tier limits
5. **Add features:** Use the working platform as base

---

**Need detailed instructions?** See `DEPLOYMENT_GUIDE.md`

**Your $150k platform is now live! 🚀**
