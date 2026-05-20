from langchain_text_splitters import RecursiveCharacterTextSplitter
from loaders import load_file
import os

try:
    from vision import process_pdf_images
except ImportError:
    process_pdf_images = None


def ingest_files(file_paths: list[str]):
    """
    Load, optionally extract images from, and chunk documents from the given file paths.

    - Skips paths that do not exist on disk (e.g., virtual YouTube entries).
    - Extracts image summaries from PDFs if the vision module is available.
    - Returns a flat list of text chunks ready for vectorstore ingestion.
    """
    all_docs = []

    for path in file_paths:
        # Guard: skip virtual/non-existent paths (e.g. YouTube fake paths)
        if not os.path.exists(path):
            print(f"Skipping non-existent path (virtual document?): {path}")
            continue

        print(f"Loading file: {path}")
        try:
            docs = load_file(path)
        except Exception as e:
            print(f"ERROR loading {path}: {e} — skipping.")
            continue

        print(f"Loaded {len(docs)} documents from {path}")
        all_docs.extend(docs)

        # Process images if it's a PDF and the vision module is available
        if process_pdf_images and path.lower().endswith('.pdf'):
            try:
                print(f"Extracting and summarizing images from {path}...")
                image_docs = process_pdf_images(path)
                print(f"Added {len(image_docs)} image summaries.")
                all_docs.extend(image_docs)
            except Exception as e:
                print(f"Skipping image extraction error for {path}: {e}")

    print(f"Total documents (text + images) before splitting: {len(all_docs)}")

    if not all_docs:
        print("WARNING: No documents loaded!")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,     # Balanced chunk size for precision
        chunk_overlap=150    # Overlap for context continuity across chunks
    )

    chunks = splitter.split_documents(all_docs)
    print(f"Total chunks after splitting: {len(chunks)}")
    return chunks