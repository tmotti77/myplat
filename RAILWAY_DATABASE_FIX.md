# 🔧 Database Connection Fix for Railway

## The Problem

Railway shows: `OSError: [Errno 101] Network is unreachable`

This happens because you're using the **direct database URL** instead of the **connection pooling URL**.

---

## The Solution (2 minutes)

### Step 1: Get the Connection Pooling URL from Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select project: **myplat-rag**
3. Click **Settings** (gear icon in sidebar)
4. Click **Database**
5. Scroll down to **Connection Pooling** section
6. Make sure **Session pooling mode** is selected (or Transaction mode)
7. Copy the connection string that looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.wkhcilgrqudlducevyud-pooler.supabase.co:5432/postgres
   ```
   **Notice the `-pooler` in the hostname!**

### Step 2: Convert to AsyncPG Format

Change the URL from:
```
postgresql://postgres:RagSecureDB2024!@db.wkhcilgrqudlducevyud-pooler.supabase.co:5432/postgres
```

To:
```
postgresql+asyncpg://postgres:RagSecureDB2024!@db.wkhcilgrqudlducevyud-pooler.supabase.co:5432/postgres
```

**Key changes:**
- Add `+asyncpg` after `postgresql`
- Make sure hostname has `-pooler` suffix

### Step 3: Update Railway Environment Variable

1. Go to Railway dashboard: https://railway.app/project
2. Click your **myplat-production** service
3. Click **Variables** tab
4. Find `DATABASE_URL`
5. **Replace** the current value with the new pooler URL:
   ```
   postgresql+asyncpg://postgres:RagSecureDB2024!@db.wkhcilgrqudlducevyud-pooler.supabase.co:5432/postgres
   ```
6. Railway will automatically redeploy

### Step 4: Wait and Check (2 minutes)

- Railway will redeploy automatically
- Check the logs - you should see:
  ```
  INFO: Application startup complete.
  ```
  Instead of the network error

---

## Why This Works

**Direct Connection:**
- Meant for long-lived connections (local development)
- Railway containers restart frequently = connection issues
- Can hit connection limits quickly

**Connection Pooling:**
- Designed for serverless/container environments
- Handles connection lifecycle automatically
- Much more reliable for Railway deployments
- Prevents "too many connections" errors

---

## Expected Result

After updating to the pooler URL, your Railway logs should show:

```
INFO: Started server process [1]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**No more "Network is unreachable" error!**

Then you can access:
- Backend API: https://myplat-production.up.railway.app/docs
- Health check: https://myplat-production.up.railway.app/health

---

## If You Can't Find Connection Pooling in Supabase

Some older Supabase projects might not show it clearly. If you can't find it:

1. Go to **Settings → Database**
2. Look for **Connection string** section
3. You'll see tabs or options for:
   - **URI** (direct connection)
   - **Pooler** or **Connection pooling** (what you need)
4. Make sure you're in **Session mode** or **Transaction mode**
5. Copy that URL and add `+asyncpg` as shown above

---

## Still Not Working?

If the pooler URL still doesn't work, there might be a different issue:

1. **Check Supabase project is active** (you already confirmed this ✅)
2. **Check password** - make sure `RagSecureDB2024!` is correct in Supabase
3. **Try IPv4 instead** - Supabase sometimes has IPv6 issues with Railway

If needed, you can also try the **Direct connection** with PgBouncer mode, but connection pooling is the recommended approach for Railway.

---

**Next:** After backend works, we'll deploy frontend to Vercel (5 minutes)
