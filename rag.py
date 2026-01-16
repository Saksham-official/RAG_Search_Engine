from langchain_community.embeddings import HuggingFaceEmbeddings
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
    # Using SMALLEST model possible for deployment
    # paraphrase-albert-small-v2 = Only 43 MB! (vs 200 MB for all-MiniLM-L6-v2)
    # Still gives good quality for RAG applications
    embeddings = HuggingFaceEmbeddings(
        model_name = "sentence-transformers/paraphrase-albert-small-v2",
        model_kwargs = {'device': 'cpu'},
        encode_kwargs = {'normalize_embeddings': True}
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
            "k": 3,  # Reduced from 10 to 3 to stay within Groq token limits
            "fetch_k": 10  # Reduced from 20 to 10
        }
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system","You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don't know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    # Using Groq as LLM provider (OpenAI removed to save dependencies)
    llm = ChatGroq(
        api_key = os.getenv("GROQ_API_KEY"),
        model_name = "llama-3.1-8b-instant",
        temperature = 0
    )
    print("✓ Using Groq as LLM provider")

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
            "k": 3,  # Number of chunks to retrieve
            "fetch_k": 10
        }
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system","You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don't know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    # Choose LLM based on environment variable
    llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if llm_provider == "openai":
        llm = ChatOpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),
            model_name = "gpt-3.5-turbo",
            temperature = 0
        )
        print("✓ Using OpenAI as LLM provider")
    elif llm_provider == "groq":
        llm = ChatGroq(
            api_key = os.getenv("GROQ_API_KEY"),
            model_name = "llama-3.1-8b-instant",
            temperature = 0
        )
        print("✓ Using Groq as LLM provider")
    else:
        raise ValueError(f"Invalid LLM_PROVIDER: {llm_provider}. Must be 'openai' or 'groq'")

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
