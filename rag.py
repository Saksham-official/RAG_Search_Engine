from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import os
import shutil

INDEX_PATH = "data/faiss_index"

def build_vectorstore(chunks, embeddings):
    """Build a FAISS vector store from document chunks."""
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def build_or_load_vectorstore(chunks = None):
    # Using HuggingFace Inference API for embeddings (no local model needed!)
    # all-MiniLM-L6-v2 via API = 0 MB local, same quality
    # Reduces deployment size from ~750MB to ~180MB by removing PyTorch
    # REQUIRES: HF token with "Make calls to Inference Providers" permission
    embeddings = HuggingFaceEndpointEmbeddings(
        huggingfacehub_api_token = os.getenv("HF_API_KEY"),
        model = "sentence-transformers/all-MiniLM-L6-v2"
    )

    # If new chunks are provided, always create a fresh index (new upload)
    if chunks is not None:
        # Delete old index to ensure fresh data
        if os.path.exists(INDEX_PATH):
            shutil.rmtree(INDEX_PATH)
        
        vectorstore = build_vectorstore(chunks, embeddings)
        vectorstore.save_local(INDEX_PATH)
        return vectorstore
    
    # Only load existing index if no new chunks provided (e.g., server restart)
    index_file = os.path.join(INDEX_PATH, "index.faiss")
    if os.path.exists(index_file):
        return FAISS.load_local(
            INDEX_PATH, 
            embeddings,
            allow_dangerous_deserialization=True
        )
    
    # No chunks and no existing index - error
    raise ValueError("No chunks provided and no existing index found.")

def build_rag_chain(vectorstore):
    """
    Build RAG chain that returns only the answer (for backward compatibility).
    """
    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {
            "k": 5,  
            "fetch_k": 15  
        }
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system","You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don't know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    llm = ChatGroq(
        api_key = os.getenv("GROQ_API_KEY"),
        model_name = "llama-3.1-8b-instant", 
        temperature = 0
    )
    print("✓ Using Groq Llama 3.1 8B (Fast Model)")

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def build_rag_chain_with_sources(vectorstore):
    """
    Build RAG chain that returns answer AND source documents for citation.
    
    EXPLANATION:
    - This version returns BOTH the answer and the source chunks
    - Source chunks include metadata (filename, page, etc.)
    - Enables transparency: users know where answers came from
    - Uses a custom function to retrieve and format sources
    """
    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {
            "k": 5,  # Increased for better context coverage
            "fetch_k": 15  # More candidates for selection
        }
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system","You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don't know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    # Using Groq Llama 3.1 8B - fast and efficient
    llm = ChatGroq(
        api_key = os.getenv("GROQ_API_KEY"),
        model_name = "llama-3.1-8b-instant",  # 8B params - fast & efficient
        temperature = 0
    )
    print("✓ Using Groq Llama 3.1 8B (Fast Model)")

    # Custom function that returns both answer and sources
    def rag_with_sources(question: str):
        # Get relevant documents using invoke (newer LangChain method)
        docs = retriever.invoke(question)
        
        # Format context from documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Get answer from LLM
        messages = prompt.format_messages(context=context, question=question)
        answer = llm.invoke(messages).content
        
        return {
            "answer": answer,
            "source_documents": docs,
            "context": context
        }
    
    return rag_with_sources
