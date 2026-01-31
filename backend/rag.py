import os
import chromadb
import instructor
from groq import Groq
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config import settings
from backend.schemas import Resume


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

groq_client = Groq(api_key=settings.groq_key)
instructor_client = instructor.from_groq(groq_client)

ch_client = chromadb.PersistentClient(path=DB_DIR)

collection = ch_client.get_or_create_collection(name="resume_date")


def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        render = PdfReader(pdf_path)
        full_text = ""

        for page in render.pages:
            full_text += page.extract_text() or ""

        return full_text

    except Exception as e:
        print(f"Error Reading PDF : {e}")
        return ""


def add_to_chromadb(file_path: str):
    try:
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)

    except Exception:
        pass

    raw_text = extract_text_from_pdf(file_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    collection.add(documents=chunks, ids=[f"id_{i}" for i in range(len(chunks))])

    return True


def analyze_resume(job_description: str) -> Resume:
    results = collection.query(query_texts=[job_description], n_results=5)

    try:
        assert results["documents"] is not None
        context = "\n\n".join(results["documents"][0])

    except Exception as e:
        print(f"ERROR: Could not retrieve context: {e}")
        raise ValueError("Resume data not found in Vector Database.")

    prompt = f"""
    You are strict Senior Technical Recruter.
    Analyze the RESUME context below against the JOB DESCRIPTION both are delemited by triple backticks
    Only give output in JSON Format according to the schema 
    
    
    RESUME CONTEXT:
    ```{context}```
    
    JOB DESCRIPTION:
    ```{job_description}```
    """

    try:
        resume_obj = instructor_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=settings.model,
            response_model=Resume,
            temperature=0.0,
            max_retries=2,
        )

    except Exception as e:
        print(f"System Error: {e}")
        raise RuntimeError("Something went wrong with the AI service.")

    return resume_obj
