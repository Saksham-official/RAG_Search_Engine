import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredFileLoader
)

def load_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".txt":
            loader = TextLoader(file_path)
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        elif ext == ".html":
            loader = UnstructuredHTMLLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path)

        print(f"Using loader: {loader.__class__.__name__}")
        docs = loader.load()
        
        if not docs:
            print(f"WARNING: Loader returned empty documents for {file_path}")
            return []

        for doc in docs:
            doc.metadata["source_file"] = os.path.basename(file_path)

        return docs
    
    except Exception as e:
        print(f"ERROR loading {file_path}: {str(e)}")
        raise Exception(f"Failed to load {file_path}: {str(e)}")