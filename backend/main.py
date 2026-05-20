import os
import sys
# Add current directory to path so that relative imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from ingest import ingest_files
from rag import build_or_load_vectorstore, build_rag_chain_with_sources, INDEX_PATH
import shutil
import os
import requests
from dotenv import load_dotenv
import traceback
import uuid
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file relative to the script location
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ============================================
# GLOBAL STATE - Enhanced for multi-document
# ============================================
vectorstore = None
rag_chain = None

# Document tracking: {doc_id: {filename, upload_time, chunk_count, path, is_virtual}}
# is_virtual=True means the file does not exist on disk (e.g. YouTube transcripts)
documents = {}

# Chat history: List of {id, question, answer, sources, timestamp}
chat_history = []

def get_all_chunks():
    """Load chunks for all tracked documents using cache where possible."""
    all_chunks = []
    import pickle
    for doc_id, doc_info in documents.items():
        cache_path = os.path.join(UPLOAD_DIR, f"{doc_id}_chunks.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    chunks = pickle.load(f)
                all_chunks.extend(chunks)
                continue
            except Exception as ce:
                print(f"Error loading cache for {doc_id}: {ce}")
        
        # Fallback to ingestion
        if os.path.exists(doc_info["path"]):
            chunks = ingest_files([doc_info["path"]])
            if chunks:
                try:
                    with open(cache_path, "wb") as f:
                        pickle.dump(chunks, f)
                except Exception as ce:
                    print(f"Error caching for {doc_id}: {ce}")
                all_chunks.extend(chunks)
    return all_chunks


# ============================================
# LIFESPAN (replaces deprecated @on_event)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application state on startup."""
    global vectorstore, rag_chain, documents, chat_history
    vectorstore = None
    rag_chain = None
    documents = {}
    chat_history = []

    # Restore documents from UPLOAD_DIR
    if os.path.exists(UPLOAD_DIR):
        for entry in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, entry)
            if os.path.isfile(file_path):
                parts = entry.split("_", 1)
                if len(parts) == 2:
                    doc_id, original_filename = parts
                    if len(doc_id) == 36:
                        if original_filename.endswith("chunks.pkl"):
                            continue
                        display_name = original_filename.replace("_", " ")
                        if original_filename.startswith("youtube_") and original_filename.endswith(".txt"):
                            video_id = original_filename[len("youtube_"):-len(".txt")]
                            display_name = f"YouTube: {video_id}"

                        documents[doc_id] = {
                            "id": doc_id,
                            "filename": display_name,
                            "upload_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                            "path": file_path,
                            "size_bytes": os.path.getsize(file_path),
                            "is_virtual": False
                        }

    # Try to load existing vectorstore if we have documents
    if documents:
        try:
            vectorstore = build_or_load_vectorstore()
            rag_chain = build_rag_chain_with_sources(vectorstore)
            print("[OK] Loaded existing vector store from disk")
        except Exception as e:
            print(f"Could not load existing vector store ({e}). Rebuilding from uploads directory...")
            try:
                chunks = get_all_chunks()
                if chunks:
                    vectorstore = build_or_load_vectorstore(chunks)
                    rag_chain = build_rag_chain_with_sources(vectorstore)
                    print("[OK] Rebuilt vector store from existing uploads using fast chunk loader")
            except Exception as re:
                print(f"Could not rebuild vector store from uploads: {re}")

    print("[OK] Server started - Using API-based embeddings (lightweight deployment!)")
    print("[OK] Ready to receive PDFs!")
    yield
    # Shutdown logic (if needed) goes here

app = FastAPI(
    title="RAG Search Engine",
    description="Intelligent document search and Q&A with AI-powered answers and source citations",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change to specific domain in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================
# Pydantic Request Models
# ============================================
class QuestionRequest(BaseModel):
    question: str

# ============================================
# SUPPORTED FILE TYPES
# ============================================
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html"}

def _enforce_chat_history_limit():
    """Keep chat_history to a maximum of 50 entries (oldest first)."""
    global chat_history
    if len(chat_history) > 50:
        chat_history = chat_history[-50:]

# ============================================
# FEATURE 1: MULTIPLE FILE SUPPORT
# ============================================

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more documents (PDF, TXT, MD, HTML).
    Each file gets a unique ID (UUID).
    Files are ADDED to existing documents (not replaced).
    Vectorstore is rebuilt to include all documents.
    """
    global vectorstore, rag_chain, documents

    uploaded_docs = []
    all_new_chunks = []

    try:
        import pickle
        # Process each uploaded file
        for file in files:
            # Validate file type
            ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
            if ext not in SUPPORTED_EXTENSIONS:
                # Re-raise as HTTPException so the outer except doesn't swallow it
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type '{ext}' for '{file.filename}'. "
                        f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                    )
                )

            # Generate unique ID for this document
            doc_id = str(uuid.uuid4())

            # Save file to disk
            safe_filename = file.filename.replace(" ", "_")
            file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{safe_filename}")
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Store document metadata
            documents[doc_id] = {
                "id": doc_id,
                "filename": file.filename,
                "upload_time": datetime.now().isoformat(),
                "path": file_path,
                "size_bytes": file_size,
                "is_virtual": False   # real file on disk
            }

            print(f"[OK] Saved: {file.filename} (ID: {doc_id})")

            # Step 2: Ingest this single file
            print(f"Ingesting: {file.filename}...")
            file_chunks = ingest_files([file_path])

            if not file_chunks:
                if os.path.exists(file_path):
                    os.remove(file_path)
                del documents[doc_id]
                raise HTTPException(
                    status_code=400,
                    detail=f"No content could be extracted from '{file.filename}'"
                )

            # Cache chunks for fast deletion/rebuilds
            cache_path = os.path.join(UPLOAD_DIR, f"{doc_id}_chunks.pkl")
            with open(cache_path, "wb") as f_cache:
                pickle.dump(file_chunks, f_cache)

            all_new_chunks.extend(file_chunks)
            uploaded_docs.append({"id": doc_id, "filename": file.filename})

        print(f"[OK] Extracted {len(all_new_chunks)} chunks total")

        # Step 3: Update global vectorstore
        # If no vectorstore exists, create one; otherwise add to existing
        if vectorstore is None:
            vectorstore = build_or_load_vectorstore(all_new_chunks)
        else:
            vectorstore.add_documents(all_new_chunks)
            # Persist immediately to the canonical path from rag.py
            vectorstore.save_local(INDEX_PATH)
        
        # Rebuild the chain to reflect new data
        rag_chain = build_rag_chain_with_sources(vectorstore)

        return {
            "message": f"Successfully uploaded {len(files)} file(s)",
            "uploaded": uploaded_docs,
            "total_documents": len(documents),
            "new_chunks_added": len(all_new_chunks)
        }

    except HTTPException:
        # Let HTTP exceptions pass through with their original status code
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error during upload: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing files: {str(e)}"
        )


@app.get("/documents")
async def list_documents():
    """
    Get list of all uploaded documents.
    Returns metadata for all documents including filename, upload time, size.
    """
    return {
        "total": len(documents),
        "documents": list(documents.values())
    }


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a specific document by its ID.
    Removes document from disk storage and rebuilds vectorstore.
    """
    global vectorstore, rag_chain, documents

    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        doc_info = documents[doc_id]

        # Delete file from disk
        if os.path.exists(doc_info["path"]):
            try:
                os.remove(doc_info["path"])
            except Exception as fe:
                print(f"Warning: Could not delete physical file {doc_info['path']}: {fe}")

        # Delete cache file from disk
        cache_path = os.path.join(UPLOAD_DIR, f"{doc_id}_chunks.pkl")
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception as ce:
                print(f"Warning: Could not delete cache file {cache_path}: {ce}")

        # Remove from tracking
        del documents[doc_id]

        # Rebuild vectorstore if documents remain
        if documents:
            remaining_chunks = get_all_chunks()
            if remaining_chunks:
                vectorstore = build_or_load_vectorstore(remaining_chunks)
                rag_chain = build_rag_chain_with_sources(vectorstore)
            else:
                vectorstore = None
                rag_chain = None
                # Clean up FAISS index files on disk
                if os.path.exists(INDEX_PATH):
                    try:
                        shutil.rmtree(INDEX_PATH)
                    except Exception as ie:
                        print(f"Warning: Could not delete index folder: {ie}")
        else:
            vectorstore = None
            rag_chain = None
            # Clean up FAISS index files on disk
            if os.path.exists(INDEX_PATH):
                try:
                    shutil.rmtree(INDEX_PATH)
                except Exception as ie:
                    print(f"Warning: Could not delete index folder: {ie}")

        return {
            "message": f"Deleted '{doc_info['filename']}'",
            "remaining_documents": len(documents)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )


# ============================================
# FEATURE 2 & 3: SOURCE CITATION + CHAT HISTORY
# ============================================

@app.post("/ask")
async def ask(body: QuestionRequest):
    """
    Ask a question and get an answer with source citations.
    Accepts a JSON body: {"question": "your question here"}
    Saves to chat history automatically.
    """
    global chat_history

    if rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Upload files first using the /upload endpoint."
        )

    try:
        question = body.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        print(f"Question: {question}")

        result = rag_chain(question)

        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])

        # Format sources for response
        sources = []
        for doc in source_docs:
            metadata = doc.metadata
            sources.append({
                "content": doc.page_content[:200] + "...",  # Preview
                "metadata": metadata
            })

        # Create history entry
        history_entry = {
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer,
            "sources": sources,
            "timestamp": datetime.now().isoformat()
        }

        chat_history.append(history_entry)
        _enforce_chat_history_limit()

        print(f"[OK] Answer generated with {len(sources)} sources")

        return {
            "answer": answer,
            "sources": sources,
            "source_count": len(sources)
        }

    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )


@app.get("/history")
async def get_history():
    """Get conversation history (last 50 entries)."""
    return {
        "total": len(chat_history),
        "history": chat_history
    }


# ============================================
# NEW APIs: YOUTUBE INGESTION & AUDIO QUERY
# ============================================

@app.post("/upload-youtube")
async def upload_youtube(url: str):
    """
    Ingest a YouTube video transcript directly into the FAISS knowledge base.
    Supports standard watch URLs and short youtu.be links.
    """
    global vectorstore, rag_chain, documents
    try:
        # Extract video ID from various YouTube URL formats
        video_id = None
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]

        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

        print(f"Fetching transcript for Video ID: {video_id}")
        # v1.x API: instantiate the class, then call .fetch()
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        
        full_text = " ".join([snippet.text for snippet in transcript])

        doc_id = str(uuid.uuid4())
        safe_filename = f"youtube_{video_id}.txt"
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{safe_filename}")

        # Save transcript text to disk (no longer virtual)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"[YOUTUBE TRANSCRIPT ID:{video_id}]\n{full_text}")

        # Track it in global state
        documents[doc_id] = {
            "id": doc_id,
            "filename": f"YouTube: {video_id}",
            "upload_time": datetime.now().isoformat(),
            "path": file_path,
            "size_bytes": len(full_text),
            "is_virtual": False
        }

        # Ingest the new file using the standard pipeline
        print(f"Ingesting YouTube transcript...")
        new_chunks = ingest_files([file_path])

        if not new_chunks:
             raise HTTPException(
                status_code=400,
                detail="No content could be extracted from YouTube transcript"
            )

        print(f"[OK] Extracted {len(new_chunks)} new chunks")

        # Cache chunks
        cache_path = os.path.join(UPLOAD_DIR, f"{doc_id}_chunks.pkl")
        import pickle
        with open(cache_path, "wb") as f_cache:
            pickle.dump(new_chunks, f_cache)

        # Update global vectorstore
        if vectorstore is None:
            vectorstore = build_or_load_vectorstore(new_chunks)
        else:
            vectorstore.add_documents(new_chunks)
            vectorstore.save_local(INDEX_PATH)

        rag_chain = build_rag_chain_with_sources(vectorstore)

        return {
            "message": "Successfully ingested YouTube video!",
            "video_id": video_id,
            "chunks_added": len(new_chunks)
        }
    except HTTPException:
        raise
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        raise HTTPException(
            status_code=400,
            detail=f"No transcript available for this video: {str(e)}"
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"YouTube Error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest YouTube video: {str(e)}")


@app.post("/ask-audio")
async def ask_audio(audio_file: UploadFile = File(...)):
    """
    Ask a question using an Audio file (Voice Note) instead of typing.
    Uses Groq's high-speed Whisper-Large-V3 API for transcription.
    """
    global chat_history
    if rag_chain is None:
        raise HTTPException(status_code=400, detail="No documents loaded. Upload PDFs/YouTube first!")

    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not groq_api_key:
        print("[ERROR] GROQ_API_KEY not found in environment.")
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not found in environment or empty.")

    print(f"DEBUG: Audio key present, length: {len(groq_api_key)}")

    try:
        # Read the uploaded audio bytes
        audio_content = await audio_file.read()

        headers = {
            "Authorization": f"Bearer {groq_api_key}"
        }

        files = {
            'file': (audio_file.filename, audio_content, audio_file.content_type),
        }
        data = {
            'model': 'whisper-large-v3'
        }

        print("Transcribing voice audio using Groq Whisper API...")
        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data
        )

        if response.status_code != 200:
            raise Exception(f"Whisper API Failed ({response.status_code}): {response.text}")

        transcription_result = response.json()
        question = transcription_result.get("text", "")
        print(f"[OK] Transcribed Question: {question}")

        if not question.strip():
            raise Exception("No speech recognized in audio file.")

        result = rag_chain(question)
        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])

        sources = []
        for doc in source_docs:
            sources.append({
                "content": doc.page_content[:200] + "...",
                "metadata": doc.metadata
            })

        chat_history.append({
            "id": str(uuid.uuid4()),
            "question": f"[🎙️ Voice Query] {question}",
            "answer": answer,
            "sources": sources,
            "timestamp": datetime.now().isoformat()
        })
        _enforce_chat_history_limit()   # Bug fix: apply the same cap as /ask

        return {
            "transcription": question,
            "answer": answer,
            "sources": sources,
            "source_count": len(sources)
        }

    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Audio Ask Error: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear-history")
async def clear_history():
    """
    Clear all chat history.
    Documents remain intact; only conversation log is reset.
    """
    global chat_history
    chat_history = []
    return {"message": "Chat history cleared"}


@app.get("/")
async def root(request: Request):
    """API Status check or Web Interface."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        frontend_html = os.path.join(os.path.dirname(BACKEND_DIR), "frontend", "index.html")
        if os.path.exists(frontend_html):
            with open(frontend_html, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return {
        "status": "online",
        "version": "2.0.0",
        "documents": len(documents),
        "history_entries": len(chat_history)
    }
