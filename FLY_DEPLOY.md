# 🚀 Fly.io Deployment Guide

## Why Fly.io?

✅ **1 GB RAM** (double Render's 512 MB)  
✅ Faster cold starts  
✅ Better free tier for ML apps  
✅ Simple deployment with `flyctl`  

---

## 📋 Deployment Steps

### 1️⃣ Install Fly.io CLI

**Windows:**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

### 2️⃣ Sign Up & Login

```bash
# Sign up (creates account)
fly auth signup

# Or login if you have account
fly auth login
```

### 3️⃣ Launch Your App

```bash
# Navigate to your project
cd c:\Users\Saksham\OneDrive\Documents\Pdf_RAG

# Launch (this creates fly.toml automatically)
fly launch

# During launch:
# - App name: rag-search-engine
# - Region: Choose closest (Singapore = sin)
# - PostgreSQL: No
# - Redis: No
```

### 4️⃣ Set Environment Variables

```bash
# Set your Groq API key
fly secrets set GROQ_API_KEY=your-groq-api-key-here

# Set LLM provider
fly secrets set LLM_PROVIDER=groq
```

### 5️⃣ Deploy!

```bash
fly deploy
```

**That's it!** Your app will be at:
```
https://rag-search-engine.fly.dev
```

---

## 🎯 After Deployment

### Access Your App

- **API:** https://rag-search-engine.fly.dev
- **Docs:** https://rag-search-engine.fly.dev/docs
- **Health:** https://rag-search-engine.fly.dev/health

### View Logs

```bash
fly logs
```

### Monitor App

```bash
fly status
```

---

## 💡 Fly.io Free Tier

**What you get:**
- 3 shared-cpu-1x VMs with 256 MB RAM each
- OR 1 VM with 1 GB RAM (recommended for your app)
- 3 GB persistent storage
- 160 GB outbound transfer

**Your app uses:**
- 1 VM with 1 GB RAM (configured in fly.toml)
- Auto-stops when idle
- Auto-starts on request

---

## 🔧 Common Commands

```bash
# Deploy updates
fly deploy

# View logs
fly logs

# SSH into app
fly ssh console

# Check status
fly status

# Stop app
fly scale count 0

# Restart app
fly scale count 1
```

---

## ⚠️ Troubleshooting

**Build fails?**
```bash
fly logs
# Check for missing dependencies
```

**App crashes?**
```bash
fly logs
# Check memory usage
```

**Slow startup?**
- First HuggingFace download takes time
- Subsequent starts are faster

---

## 📊 Cost

**Free tier is enough for demos!**
- Upgrade only if you need:
  - 24/7 uptime
  - More memory
  - Multiple regions

---

**Your app will be MUCH faster on Fly.io than Render!** 🚀
