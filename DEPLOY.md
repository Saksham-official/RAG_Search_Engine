# 🚀 Manual Render Deployment Guide

## Quick Deploy Instructions

### 1️⃣ Render Dashboard Settings

**Build Command:**
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**Start Command:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```
GROQ_API_KEY = your-groq-api-key-here
LLM_PROVIDER = groq
PYTHON_VERSION = 3.11.0
```

### 2️⃣ Configuration

- **Name:** `rag-search-engine`
- **Runtime:** Python 3
- **Plan:** Free
- **Branch:** main
- **Root Directory:** (leave empty)

### 3️⃣ Deploy

Click "Create Web Service" and wait 5-10 minutes.

Your app will be at: `https://rag-search-engine.onrender.com`

---

## ⚠️ Troubleshooting

**Port binding error?**
- Make sure start command uses `$PORT` variable
- Use the exact command above

**Build fails?**
- Check build logs
- Verify all dependencies in requirements.txt

**Out of memory?**
- Free tier has 512 MB RAM limit
- Reduce chunk size if needed

---

That's it! 🎉
