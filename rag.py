from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun

import os
import shutil

INDEX_PATH = "data/faiss_index"


def build_or_load_vectorstore(chunks=None):
    """
    Build a new FAISS vectorstore from chunks, or load one from disk.
    
    - If `chunks` is provided, always builds a fresh index (replacing any existing one).
    - If `chunks` is None, loads the existing on-disk index.
    - Raises ValueError if neither chunks nor an existing index are available.
    """
    hf_api_key = os.getenv("HF_API_KEY")
    if not hf_api_key:
        raise ValueError("HF_API_KEY environment variable is not set.")

    # Using HuggingFace Inference API for embeddings (no local model needed!)
    # Requires an active HF token with 'Inference' permissions in .env
    embeddings = HuggingFaceEndpointEmbeddings(
        huggingfacehub_api_token=hf_api_key,
        model="sentence-transformers/all-MiniLM-L6-v2"
    )

    # If new chunks are provided, always create a fresh index (new upload)
    if chunks is not None:
        # Delete old index to ensure fresh data
        if os.path.exists(INDEX_PATH):
            shutil.rmtree(INDEX_PATH)

        vectorstore = FAISS.from_documents(chunks, embeddings)
        os.makedirs(INDEX_PATH, exist_ok=True)
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

    # No chunks and no existing index
    raise ValueError("No chunks provided and no existing FAISS index found.")


def build_rag_chain(vectorstore):
    """
    Build a basic RAG chain that returns only the answer string.
    Kept for backward compatibility.
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don't know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    llm = ChatGroq(
        api_key=groq_api_key,
        model_name="llama-3.1-8b-instant",
        temperature=0
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
    Build a RAG chain that returns answer AND source documents for citation.
    Supports Multimodal RAG with Vision summaries and real-time DuckDuckGo search.
    """
    # Use MMR (Maximal Marginal Relevance) for diverse, non-redundant results.
    # fetch_k is a valid MMR parameter (pre-selection pool size).
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,       # Final docs returned to LLM
            "fetch_k": 20  # Candidate pool for MMR selection
        }
    )

    system_prompt = (
        "You are an intelligent, helpful expert assistant. "
        "Use the provided retrieved context (and images if applicable) to answer the user's question clearly and comprehensively. "
        "Synthesize the information rather than just quoting it rigidly. "
        "If the answer isn't fully covered by the context, explain what you found and what is missing, "
        "rather than just saying 'I don't know'."
    )

    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set or empty.")

    llm = ChatGroq(
        api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3
    )
    print("✓ Using Groq Llama 3.3 70B Versatile for Generation")

    # web_search = DuckDuckGoSearchRun()  # Disabled due to library compatibility

    def rag_with_sources(question: str) -> dict:
        docs = retriever.invoke(question)

        # Build text context from retrieved documents
        context_parts = []
        for doc in docs:
            # Check if this document is an image summary with a valid file on disk
            img_path = doc.metadata.get("image_path", "")
            if img_path and os.path.exists(img_path):
                context_parts.append(
                    f"[Visual content from: {os.path.basename(img_path)}]\n{doc.page_content}"
                )
            else:
                context_parts.append(doc.page_content)

        context = "\n\n".join(context_parts)

        # Real-time internet fallback — [DISABLED FOR COMPATIBILITY]
        # try:
        #     print("Fetching real-time web context via DuckDuckGo...")
        #     web_results = web_search.invoke(question)
        #     if web_results and len(web_results.strip()) > 10:
        #         context += f"\n\n--- SUPPLEMENTARY REAL-TIME WEB SEARCH RESULTS ---\n{web_results}"
        # except Exception as e:
        #     print(f"Web search failed (skipping): {e}")

        human_content = f"Context information:\n{context}\n\nUser Question: {question}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        answer = llm.invoke(messages).content

        return {
            "answer": answer,
            "source_documents": docs,
            "context": context
        }

    return rag_with_sources
