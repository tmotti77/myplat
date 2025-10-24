# ▲ Vercel Frontend Deployment - Step by Step

**Time:** 3-5 minutes
**Cost:** FREE forever (for hobby projects)

---

## 🎯 STEP 1: Import Project

1. Go to: https://vercel.com/new
2. You should see "Import Git Repository"
3. Find **"tmotti77/myplat"** in the list
   - If you don't see it, click **"Add GitHub Account"** and authorize
4. Click **"Import"**

---

## 🎯 STEP 2: Configure Project

Vercel will auto-detect Next.js, but you need to set the root directory:

1. **Framework Preset:** Should auto-select "Next.js" ✓
2. **Root Directory:** Click "Edit" and type: `frontend`
3. **Build Command:** Leave as default (`npm run build`)
4. **Output Directory:** Leave as default (`.next`)
5. **Install Command:** Leave as default (`npm install`)

---

## 🎯 STEP 3: Add Environment Variable

This is critical - your frontend needs to know where the backend is!

1. Scroll down to **"Environment Variables"** section
2. Add ONE variable:

   **Key:** `NEXT_PUBLIC_API_URL`

   **Value:** Your Railway backend URL (from Railway deployment)

   Example: `https://myplat-production.up.railway.app`

   ⚠️ **Important:** NO trailing slash! Don't add `/` at the end!

3. Leave **"Environment"** as "Production" (default)

---

## 🎯 STEP 4: Deploy!

1. Click **"Deploy"** button (bottom)
2. Vercel will start building
3. Wait 2-4 minutes
4. Look for **"Congratulations!"** message

---

## 🎯 STEP 5: Get Your Frontend URL

1. After successful deployment, you'll see your live URL
2. Usually looks like: `https://myplat.vercel.app` or `https://myplat-xxx.vercel.app`
3. **COPY THIS URL** - you'll need it to update CORS!

---

## 🎯 STEP 6: Update CORS in Railway

Now you need to tell the backend to accept requests from your frontend:

1. Go back to **Railway dashboard**
2. Click on your service
3. Click **"Variables"** tab
4. Find the `CORS_ORIGINS` variable
5. Update it to:
   ```bash
   ["https://myplat.vercel.app","https://myplat-production.up.railway.app"]
   ```
   (Replace with YOUR actual Vercel URL and Railway URL)

6. Railway will automatically redeploy (wait 1-2 minutes)

---

## ✅ STEP 7: Test Your Frontend

1. Open your Vercel URL: `https://myplat.vercel.app`
2. **You should see:** Login page with MyPlat branding!
3. Try clicking around - pages should load

---

## 🎉 SUCCESS!

Your frontend is now live!

**Save your URLs:**
```
Frontend: https://myplat.vercel.app
Backend: https://myplat-production.up.railway.app
```

---

## 🧪 STEP 8: Test Full Workflow

Now let's make sure everything works end-to-end:

### **1. Create Account**
- Click "Sign Up" or "Create Account"
- Fill in email and password
- Submit

### **2. Login**
- Use the credentials you just created
- Should redirect to dashboard

### **3. Upload Document**
- Go to "Documents" or "Upload"
- Upload a PDF or text file
- Should show upload progress

### **4. Search**
- Go to "Search" page
- Type a query about your document
- Should return relevant results

### **5. Chat**
- Go to "Chat" page
- Ask a question about your document
- Should get AI response with citations

---

## 🐛 Troubleshooting

**"Network Error" or "API Error"**
- Check CORS_ORIGINS is updated in Railway
- Verify NEXT_PUBLIC_API_URL in Vercel settings
- Make sure Railway backend is deployed successfully
- Test backend directly: `https://your-backend.up.railway.app/docs`

**Pages Not Loading**
- Check Vercel deployment succeeded
- Look at Vercel deployment logs for errors
- Check root directory is set to `frontend`

**Can't Create Account**
- Check Railway backend logs for errors
- Verify database connection in Railway
- Test `/health` endpoint on backend

**Upload Not Working**
- Check Supabase storage bucket is created
- Verify SUPABASE_KEY is set in Railway
- Check browser console for errors

---

## 🎨 Optional: Custom Domain

Want to use your own domain like `myplatform.com`?

### **In Vercel:**
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as shown
4. Wait 5-10 minutes for propagation

### **In Railway:**
1. Go to Settings → Domains
2. Add custom domain for API (e.g., `api.myplatform.com`)
3. Update DNS records
4. Update CORS_ORIGINS and Vercel env var with new URLs

---

## 🎉 YOU'RE LIVE!

Your full-stack RAG platform is now running in production!

**What you have:**
- ✅ Frontend: Fast, global CDN (Vercel)
- ✅ Backend: 51 working API endpoints (Railway)
- ✅ Database: PostgreSQL with pgvector (Supabase)
- ✅ Storage: Document storage (Supabase)
- ✅ Cache: Redis (Upstash)
- ✅ AI: OpenAI GPT-4 integration

**Monthly cost:** $32-50 (or FREE with free tiers)

**Next steps:**
- Add more documents
- Invite team members
- Monitor usage in dashboards
- Scale when needed

---

**Congratulations! You just deployed a production RAG platform! 🚀**
