import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

PERSIST_DIRECTORY = 'Dir'
COLLECTION_NAME = 'Docs'

def build_vectorstore_from_pdf(pdf_path: str):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    pdf_loader = PyPDFLoader(pdf_path)
    pages = pdf_loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    pages_split = text_splitter.split_documents(pages)
    if not os.path.exists(PERSIST_DIRECTORY):
        os.makedirs(PERSIST_DIRECTORY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    vectorstore = Chroma.from_documents(documents=pages_split, embedding=embeddings, persist_directory=PERSIST_DIRECTORY, collection_name=COLLECTION_NAME)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    return retriever, vectorstore
