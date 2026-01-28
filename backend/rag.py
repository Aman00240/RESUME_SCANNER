import os
import chromadb
from app.config import settings
from groq import Groq
from langchain_text_splitters import RecursiveCharacterTextSplitter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

groq_client = Groq(api_key=settings.groq_key)

ch_client = chromadb.PersistentClient(path=DB_DIR)

collection = ch_client.get_or_create_collection(name="resume_date")
