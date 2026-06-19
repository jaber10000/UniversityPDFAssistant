import os
import streamlit as st
from dotenv import load_dotenv

import google.generativeai as genai

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------- ENV ----------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY missing!")

genai.configure(api_key=GOOGLE_API_KEY)

# ---------------- UI ----------------
st.set_page_config(page_title="PDF Assistant", page_icon="📚")
st.title("📚 PDF RAG Assistant (Free Tier Compatible)")

# ---------------- SESSION ----------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- UPLOAD ----------------
pdf = st.file_uploader("Upload PDF", type="pdf")

if pdf:
    with open("temp.pdf", "wb") as f:
        f.write(pdf.read())

    loader = PyPDFLoader("temp.pdf")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    st.session_state.vectorstore = vectorstore

    st.success("✅ PDF Ready!")

# ---------------- CHAT ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Ask question...")

if question and st.session_state.vectorstore:

    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    retriever = st.session_state.vectorstore.as_retriever(k=4)
    docs = retriever.invoke(question)

    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
You are a helpful assistant.

Use only the context below.

Context:
{context}

Question:
{question}
"""

    # ✅ Use gemini-1.0-pro (still available on free tier)
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    response = model.generate_content(prompt)
    answer = response.text

    with st.chat_message("assistant"):
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
