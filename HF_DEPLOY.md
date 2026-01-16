# 🚀 Deploy Backend to Hugging Face Spaces (FREE)

## ✅ Why Hugging Face Spaces?

- 🆓 **100% Free** - No credit card required!
- 🔥 **2 GB RAM** - Perfect for your RAG backend
- ⚡ **Fast for ML apps** - Optimized for HuggingFace models
- 🌐 **Public API** - Get shareable URL instantly

---

## 📋 Step-by-Step Deployment

### 1️⃣ Create Hugging Face Account

- Go to: https://huggingface.co/join
- Sign up for free (no CC needed!)

### 2️⃣ Create New Space

1. Go to: https://huggingface.co/new-space
2. Fill in:
   - **Space name:** `rag-search-engine`
   - **License:** MIT
   - **SDK:** Docker
   - **Private:** No (keep public)

3. Click "Create Space"

### 3️⃣ Prepare Files

**Rename HF_README.md to README.md:**

```bash
# In your project folder
move HF_README.md README_HF.md
copy README.md README_GITHUB.md
copy README_HF.md README.md
```

This README.md will be shown on HF Spaces.

### 4️⃣ Push to Hugging Face

**Option A: Using Git (Recommended)**

```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR-USERNAME/rag-search-engine

# Make sure you have the right files
git add .
git commit -m "Deploy to Hugging Face Spaces"

# Push to HF
git push hf main
```

**Option B: Upload Files Manually**

1. Go to your Space page
2. Click "Files" tab
3. Click "Add file" → "Upload files"
4. Upload:
   - `Dockerfile`
   - `main.py`
   - `rag.py`
   - `ingest.py`
   - `loaders.py`
   - `requirements.txt`
   - `.gitignore`
   - `README.md` (the renamed HF_README.md)

### 5️⃣ Add Secrets

1. Go to your Space → Settings
2. Scroll to "Repository secrets"
3. Add:
   - **Name:** `GROQ_API_KEY`
   - **Value:** your-groq-api-key
4. Add:
   - **Name:** `LLM_PROVIDER`
   - **Value:** `groq`

### 6️⃣ Wait for Build

- HF will automatically build and deploy
- Takes 5-10 minutes first time
- Watch the "Build" tab for logs

### 7️⃣ Access Your API

Your backend will be live at:
```
https://YOUR-USERNAME-rag-search-engine.hf.space
```

**API Documentation:**
```
https://YOUR-USERNAME-rag-search-engine.hf.space/docs
```

---

## 🌐 Enable CORS for Frontend

After deployment, your frontend needs CORS enabled. 

**HF automatically handles CORS**, but if you need custom CORS:

Edit `main.py` to add:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎯 Testing Your Backend

```bash
# Health check
curl https://YOUR-USERNAME-rag-search-engine.hf.space/

# API docs (open in browser)
https://YOUR-USERNAME-rag-search-engine.hf.space/docs
```

---

## 📊 Monitoring

- **Build logs:** Space page → "Build" tab
- **Runtime logs:** Space page → "Logs" tab
- **Restart:** Space settings → "Factory reboot"

---

## 💡 Important Notes

### File Structure

Make sure these files are in root:
```
/
├── Dockerfile          ✅
├── README.md           ✅ (renamed from HF_README.md)
├── requirements.txt    ✅
├── main.py            ✅
├── rag.py             ✅
├── ingest.py          ✅
├── loaders.py         ✅
└── .gitignore         ✅
```

### Don't Include:
- ❌ `.env` (use Secrets instead)
- ❌ `uploads/` folder
- ❌ `data/` folder
- ❌ `.venv/`

### Port Configuration

- HF Spaces requires port **7860**
- Already configured in Dockerfile ✅

---

## 🔄 Update Your Deployed App

```bash
# Make changes locally
git add .
git commit -m "Update backend"

# Push to HF
git push hf main

# HF will auto-rebuild
```

---

## 🎉 After Deployment

You'll have:
- ✅ Free backend API
- ✅ Public URL for frontend to call
- ✅ 2 GB RAM (plenty!)
- ✅ Auto-scaling
- ✅ HTTPS by default

**Now build your frontend and connect it!** 🚀

---

## 📝 Frontend Connection Example

```javascript
const API_BASE = "https://YOUR-USERNAME-rag-search-engine.hf.space";

// Upload PDF
const formData = new FormData();
formData.append('files', pdfFile);
fetch(`${API_BASE}/upload`, {
  method: 'POST',
  body: formData
});

// Ask question
fetch(`${API_BASE}/ask?question=${question}`)
  .then(res => res.json())
  .then(data => console.log(data.answer));
```

---

**Your backend will be live and free forever on HF Spaces!** 🎯
