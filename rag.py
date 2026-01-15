from langchain_community.embeddings import HuggingfaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import os

def build_vectorstore(chunks):
    embeddings = HuggingfaceEmbeddings(
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def build_rag_chain(vectorstore):
    retriever = vectorstore.as_retriver(
    search_type = "mmr",
    search_kwargs = {
        "k" : 5
        }
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system","You are a factual assistant. Answer ONLY using the provided context. "
         "If the answer is not present, say: 'I don’t know based on the document.'"),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])

    llm = ChatGrok(
        api_key = os.getenv("GROQ_API_KEY"),
        model_name = "llama-3.1-8b-instant",
        temperature = 0
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
