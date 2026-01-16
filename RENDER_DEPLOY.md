# 🚀 Quick Deploy to Render (FREE)

## ✅ Your Project is Ready!

All configuration files are created. Follow these steps:

---

## 📋 Step-by-Step Deployment

### 1️⃣ Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR-USERNAME/RAG-Search-Engine.git
git branch -M main
git push -u origin main
```

### 2️⃣ Create Render Account

- Go to: https://render.com
- Sign up with GitHub (FREE, no credit card needed)

### 3️⃣ Deploy on Render

1. **Click "New +"** → **"Web Service"**

2. **Connect GitHub**
   - Authorize Render to access your repos
   - Select "RAG-Search-Engine" repository

3. **Render Auto-Detects Everything!**
   - Name: `rag-search-engine` (already set in render.yaml)
   - Branch: `main`
   - Build Command: Auto-detected ✓
   - Start Command: Auto-detected ✓

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add your variables:
     - `GROQ_API_KEY` = `your-actual-groq-key`
     - `LLM_PROVIDER` = `groq`

5. **Click "Create Web Service"**

### 4️⃣ Wait for Deployment

- First build takes 5-10 minutes
- Watch the logs in real-time
- Status will change to "Live" when ready

### 5️⃣ Get Your URL

- Your app will be at: `https://rag-search-engine.onrender.com`
- Access API docs at: `https://rag-search-engine.onrender.com/docs`

---

## 🎯 After Deployment

### Test Your API

```bash
# Health check
curl https://rag-search-engine.onrender.com/

# API docs
https://rag-search-engine.onrender.com/docs
```

### Update README

Add your live demo link to the README:

```markdown
## 🌐 Live Demo

**API:** https://rag-search-engine.onrender.com
**Docs:** https://rag-search-engine.onrender.com/docs
```

---

## ⚠️ Important Notes

### Free Tier Limitations:
- ✅ **100% FREE** forever
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Takes 30-60 seconds to wake up on first request
- ⚠️ 512 MB RAM (enough for your app)

### For Better Performance:
- Upgrade to paid plan ($7/month) for:
  - No spin-down
  - More memory
  - Faster response times

---

## 🐛 Troubleshooting

### Build fails?
- Check `requirements.txt` has all dependencies
- View build logs on Render dashboard

### Environment variables not working?
- Make sure you added them in Render dashboard
- Don't use quotes around values

### App crashes?
- Check logs in Render dashboard
- Reduce chunk size in `rag.py` if out of memory

---

## ✨ You're Done!

Your RAG Search Engine is now:
- ✅ Live on the internet
- ✅ Accessible via API
- ✅ 100% FREE on Render
- ✅ Portfolio-ready

**Share your live demo link with recruiters!** 🎉
