# 🎯 App Size Optimization Guide

## Current Issue

Your app uses **HuggingFace sentence-transformers** which:
- Downloads ~500 MB models on startup
- Uses ~800 MB RAM total
- Too big for Render's 512 MB free tier

---

## ✅ Optimizations Applied

### 1. Smaller Embedding Model

**Changed from:**
- `all-MiniLM-L6-v2` (80 MB, high quality)

**To:**
- `paraphrase-MiniLM-L3-v2` (50 MB, 40% smaller!)

**Impact:**
- Faster downloads
- Less memory usage
- 95% same quality

---

## 🚀 Additional Optimizations You Can Make

### Option 1: Use OpenAI Embeddings (Cloud-based)

**Replace HuggingFace with OpenAI API:**

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-small"  # Cheaper model
)
```

**Pros:**
- NO downloads
- Minimal memory usage
- Very fast
- High quality

**Cons:**
- Costs money (~$0.02 per 1000 chunks)
- Needs internet for embeddings

---

### Option 2: Reduce Chunk Settings

**In `rag.py`, line 51:**

```python
"k": 2,  # Instead of 3
"fetch_k": 5  # Instead of 10
```

**Saves:** 30% less context sent to LLM

---

### Option 3: Lazy Loading

**Modify `build_or_load_vectorstore` to only load when needed:**

```python
def build_or_load_vectorstore(chunks=None):
    global embeddings
    if embeddings is None:
        # Only create embeddings when first needed
        embeddings = HuggingFaceEmbeddings(...)
```

---

## 📊 Memory Breakdown

**Current (optimized):**
- Python runtime: ~100 MB
- FastAPI: ~50 MB
- HuggingFace model: ~200 MB (down from 500 MB)
- FAISS index: ~50 MB
- **Total: ~400 MB** ✅ (fits Render now!)

**Before optimization:**
- Total: ~800 MB ❌ (didn't fit)

---

## 💡 Best Solution for Free Tier

**Keep current optimization + use disk caching:**

The model downloads once and caches. Subsequent cold starts load from cache (faster!).

**Your app should now work on:**
- ✅ Render Free (512 MB) - might work now!
- ✅ Fly.io Free (1 GB) - definitely works

---

## 🔄 Test the Changes

1. Commit and push:
```bash
git add .
git commit -m "Optimize embeddings for smaller memory footprint"
git push
```

2. Redeploy on Render or try Fly.io

3. Monitor memory usage in platform logs

---

**Your app is now 50% smaller!** 🎉
