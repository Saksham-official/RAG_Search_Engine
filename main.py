from fastapi import FastAPI, UploadFile, File
from ingest import load_and_split_pdf
from rag import build_vectorstore, build_rag_chain
import shutil
import os

app = FastAPI()

vectorstore = None
rag_chain = None

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    


