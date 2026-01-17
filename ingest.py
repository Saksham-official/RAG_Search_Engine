from langchain_text_splitters import RecursiveCharacterTextSplitter
from loaders import load_file

def ingest_files(file_paths: list[str]):
    all_docs = []

    for path in file_paths:
        print(f"Loading file: {path}")
        docs = load_file(path)
        print(f"Loaded {len(docs)} documents from {path}")
        all_docs.extend(docs)
   
    print(f"Total documents before splitting: {len(all_docs)}")
    
    if len(all_docs) == 0:
        print("WARNING: No documents loaded!")
        return []
    
    # Optimized chunking for balanced model
    # Smaller chunks = more precise context matching
    # Better for improved embedding model quality
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,  # Reduced for precision (was 2000)
        chunk_overlap = 150  # Optimal overlap for context continuity
    )

    chunks = splitter.split_documents(all_docs)
    print(f"Total chunks after splitting: {len(chunks)}")
    return chunks