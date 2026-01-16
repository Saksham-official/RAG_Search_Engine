from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from ingest import ingest_files
from rag import build_or_load_vectorstore, build_rag_chain_with_sources
import shutil
import os
from dotenv import load_dotenv
import traceback
import uuid
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="RAG Search Engine",
    description="Intelligent document search and Q&A with AI-powered answers and source citations",
    version="2.0.0"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================
# GLOBAL STATE - Enhanced for multi-document
# ============================================
vectorstore = None
rag_chain = None

# Document tracking: {doc_id: {filename, upload_time, chunk_count, path}}
documents = {}

# Chat history: List of {id, question, answer, sources, timestamp}
chat_history = []

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global vectorstore, rag_chain, documents, chat_history
    vectorstore = None
    rag_chain = None
    documents = {}
    chat_history = []
    print("✓ Server started - Ready to receive PDFs!")

# ============================================
# FEATURE 1: MULTIPLE FILE SUPPORT
# ============================================

@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF files.
    
    EXPLANATION:
    - Now accepts a LIST of files instead of single file
    - Each file gets a unique ID (UUID)
    - Files are ADDED to existing documents (not replaced)
    - Vectorstore is rebuilt to include all documents
    """
    global vectorstore, rag_chain, documents
    
    try:
        uploaded_docs = []
        all_file_paths = []
        
        # Process each uploaded file
        for file in files:
            # Validate file type
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a PDF"
                )
            
            # Generate unique ID for this document
            doc_id = str(uuid.uuid4())
            
            # Save file to disk
            file_path = f"{UPLOAD_DIR}/{doc_id}_{file.filename}"
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
                "size_bytes": file_size
            }
            
            all_file_paths.append(file_path)
            uploaded_docs.append({
                "id": doc_id,
                "filename": file.filename
            })
            
            print(f"✓ Saved: {file.filename} (ID: {doc_id})")
        
        # Process ALL files (new + existing)
        all_existing_paths = [doc["path"] for doc in documents.values()]
        
        print(f"Processing {len(all_existing_paths)} total documents...")
        chunks = ingest_files(all_existing_paths)
        
        if not chunks:
            raise HTTPException(
                status_code=500,
                detail="No content extracted from PDFs"
            )
        
        # Update chunk counts in metadata
        # (This is approximate - actual implementation would track per-doc)
        total_chunks = len(chunks)
        print(f"✓ Extracted {total_chunks} total chunks")
        
        # Rebuild vectorstore with all documents
        vectorstore = build_or_load_vectorstore(chunks)
        rag_chain = build_rag_chain_with_sources(vectorstore)
        
        return {
            "message": f"Successfully uploaded {len(files)} file(s)",
            "uploaded": uploaded_docs,
            "total_documents": len(documents),
            "total_chunks": total_chunks
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error during upload: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDFs: {str(e)}"
        )

@app.get("/documents")
async def list_documents():
    """
    Get list of all uploaded documents.
    
    EXPLANATION:
    - Returns metadata for all documents
    - Shows filename, upload time, size
    - Users can see what documents are in the system
    """
    return {
        "total": len(documents),
        "documents": list(documents.values())
    }

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a specific document.
    
    EXPLANATION:
    - Removes document from storage
    - Rebuilds vectorstore without that document
    - Useful for managing document library
    """
    global vectorstore, rag_chain, documents
    
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Get document info
        doc_info = documents[doc_id]
        
        # Delete file from disk
        if os.path.exists(doc_info["path"]):
            os.remove(doc_info["path"])
        
        # Remove from tracking
        del documents[doc_id]
        
        # Rebuild vectorstore if documents remain
        if documents:
            remaining_paths = [doc["path"] for doc in documents.values()]
            chunks = ingest_files(remaining_paths)
            vectorstore = build_or_load_vectorstore(chunks)
            rag_chain = build_rag_chain_with_sources(vectorstore)
        else:
            # No documents left
            vectorstore = None
            rag_chain = None
        
        return {
            "message": f"Deleted {doc_info['filename']}",
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
async def ask(question: str):
    """
    Ask a question and get an answer with source citations.
    
    EXPLANATION:
    - Now returns answer + sources (which document/page)
    - Automatically saves to chat history
    - Shows where the answer came from (transparency!)
    """
    global chat_history
    
    if rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="Upload PDFs first using the /upload endpoint"
        )
    
    try:
        print(f"Question: {question}")
        
        # Get answer WITH sources (rag_chain is now a function)
        result = rag_chain(question)
        
        # Extract answer and sources
        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])
        
        # Format sources for response
        sources = []
        for doc in source_docs:
            # Get metadata from the document chunk
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
        
        # Save to chat history (keep last 50)
        chat_history.append(history_entry)
        if len(chat_history) > 50:
            chat_history.pop(0)  # Remove oldest
        
        print(f"✓ Answer generated with {len(sources)} sources")
        
        return {
            "answer": answer,
            "sources": sources,
            "source_count": len(sources)
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )

@app.get("/history")
async def get_history():
    """
    Get conversation history.
    
    EXPLANATION:
    - Returns all saved Q&A pairs
    - Shows timestamps and sources
    - Useful for reviewing past conversations
    """
    return {
        "total": len(chat_history),
        "history": chat_history
    }

@app.delete("/clear-history")
async def clear_history():
    """
    Clear all chat history.
    
    EXPLANATION:
    - Resets conversation history
    - Documents remain intact
    - Fresh start for new conversation
    """
    global chat_history
    chat_history = []
    return {"message": "Chat history cleared"}

@app.get("/")
async def root():
    """API Status check."""
    return {
        "status": "online",
        "version": "2.0.0",
        "documents": len(documents),
        "history_entries": len(chat_history)
    }
