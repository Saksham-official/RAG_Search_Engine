---
title: RAG Search Engine API
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# RAG Search Engine - Backend API

## 🚀 API Endpoints

This is the backend API for the RAG Search Engine. It provides intelligent document search and question-answering capabilities.

### Base URL
```
https://your-space-name.hf.space
```

### Available Endpoints

- `GET /` - API status
- `GET /docs` - Interactive API documentation (Swagger UI)
- `POST /upload` - Upload PDF files
- `GET /documents` - List all documents
- `DELETE /documents/{id}` - Delete a document
- `POST /ask` - Ask questions about uploaded documents
- `GET /history` - Get chat history
- `DELETE /clear-history` - Clear chat history

### API Documentation

Access the complete API documentation at:
```
https://your-space-name.hf.space/docs
```

### Example Usage

```bash
# Upload a PDF
curl -X POST "https://your-space-name.hf.space/upload" \
  -F "files=@document.pdf"

# Ask a question
curl -X POST "https://your-space-name.hf.space/ask?question=What is the main topic?"
```

### Features

- ✅ Multiple PDF upload support
- ✅ Source citation with page numbers
- ✅ Chat history tracking
- ✅ Semantic search using embeddings
- ✅ AI-powered answers (Groq/OpenAI)

### Tech Stack

- FastAPI
- LangChain
- FAISS Vector Store
- HuggingFace Embeddings
- Groq LLM

---

Check out the configuration: [README.md](https://github.com/your-username/RAG_Search_Engine)
