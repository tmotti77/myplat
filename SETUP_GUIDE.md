# 🚀 Hybrid RAG Platform - Complete Setup Guide

## 📋 **Step 1: Docker Desktop Setup**

✅ **You've already opened Docker Desktop!**

Now enable WSL integration:
1. **Docker Desktop** → **Settings** → **Resources** → **WSL Integration**
2. **Enable integration** with your WSL distro
3. **Apply & Restart**

## 🔑 **Step 2: Get Your API Keys & Secrets**

### **OpenAI API Key** (REQUIRED)
1. Go to: https://platform.openai.com/api-keys
2. **Sign in** to your OpenAI account (or create one)
3. Click **"Create new secret key"**
4. **Name it**: "RAG Platform"
5. **Copy the key** (starts with `sk-...`)
6. **IMPORTANT**: This is the only time you'll see it!

**Which API do you need?**
- ✅ **GPT-4 or GPT-3.5 API access**
- ✅ **Text Embeddings API access**
- 💰 **Cost**: ~$0.10-1.00 per day for testing

### **Database Password** (Your Choice)
- **You choose this!** Something secure like: `MySecureDB2024!`
- **This is NOT your Windows password**
- **It's a new password just for this database**

### **JWT Secrets** (Auto-Generated)
**I'll generate these for you:**

```bash
# JWT Secret (32+ characters)
JWT_SECRET_KEY="rag_platform_jwt_secret_2024_super_secure_key_xyz123"

# JWT Refresh Secret (different from above)
JWT_REFRESH_SECRET_KEY="rag_refresh_token_ultra_secure_2024_abc789"

# General Secret Key
SECRET_KEY="rag_app_master_secret_key_2024_def456"

# Encryption Keys (exactly 32 characters)
ENCRYPTION_KEY="12345678901234567890123456789012"
MASTER_ENCRYPTION_KEY="abcdefghijklmnopqrstuvwxyz123456"
```

## ⚙️ **Step 3: Update Your .env File**

Open your `.env` file and replace these lines:

```env
# Replace this line:
OPENAI_API_KEY="sk-your-openai-api-key-here"
# With your real API key:
OPENAI_API_KEY="sk-YOUR_ACTUAL_KEY_HERE"

# Replace this line:
DATABASE_URL="postgresql+asyncpg://rag_user:your_password_here@localhost:5432/rag_platform"
# With (choose your password):
DATABASE_URL="postgresql+asyncpg://rag_user:MySecureDB2024!@localhost:5432/rag_platform"

# Replace these security keys:
JWT_SECRET_KEY="rag_platform_jwt_secret_2024_super_secure_key_xyz123"
JWT_REFRESH_SECRET_KEY="rag_refresh_token_ultra_secure_2024_abc789"
SECRET_KEY="rag_app_master_secret_key_2024_def456"
ENCRYPTION_KEY="12345678901234567890123456789012"
MASTER_ENCRYPTION_KEY="abcdefghijklmnopqrstuvwxyz123456"
```

## 🧪 **Step 4: Test the Platform**

### **Start Backend Services:**
```powershell
# In your main directory:
./start-simple.ps1
```

### **Test API Health:**
Open browser to: http://localhost:8000/health
**Expected result:** `{"status": "healthy"}`

### **View API Documentation:**
Open browser to: http://localhost:8000/docs
**Expected result:** Interactive API docs

### **Start Frontend:**
```powershell
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open browser to: http://localhost:3000

## 🔧 **Step 5: Default Login Credentials**

When the platform starts, use these to login:
- **Email:** `admin@example.com`
- **Password:** `admin123!`

## 🆘 **Troubleshooting**

### **"Docker command not found"**
- Restart PowerShell after enabling WSL integration
- Try: `docker --version`

### **"OpenAI API Error"**
- Check your API key is correct
- Verify you have credits in OpenAI account
- Check: https://platform.openai.com/usage

### **"Database Connection Error"**
- Make sure Docker containers are running
- Check: `docker ps` (should show postgres container)

### **"Frontend Won't Start"**
- Try: `npm install --force`
- Or: `rm -rf node_modules && npm install`

## 💡 **What You'll Be Able to Test**

1. **✅ User Authentication** - Login/logout
2. **✅ Document Upload** - PDF, Word, text files
3. **✅ AI Chat** - Ask questions about your documents
4. **✅ Search** - Find information in uploaded docs
5. **✅ Dashboard** - View statistics and activity

## 📞 **Need Help?**

If anything doesn't work:
1. **Check Docker** is running: `docker ps`
2. **Check logs**: `docker-compose -f docker-compose.simple.yml logs`
3. **API health**: http://localhost:8000/health
4. **Tell me the specific error message**

---

**Ready to start? Let's test step by step!** 🚀