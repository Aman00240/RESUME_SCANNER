import os
import chromadb
import instructor
from groq import Groq
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config import settings
from backend.schemas import Resume

from chromadb import Documents, EmbeddingFunction, Embeddings
from fastembed import TextEmbedding


class CustomFastEmbedEF(EmbeddingFunction):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = TextEmbedding(model_name=model_name)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings_generator = self.model.embed(input)

        return [e.tolist() for e in embeddings_generator]


ef = CustomFastEmbedEF()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

groq_client = Groq(api_key=settings.groq_key)
instructor_client = instructor.from_groq(groq_client)

ch_client = chromadb.PersistentClient(path=DB_DIR)

collection = ch_client.get_or_create_collection(
    name="resume_date",
    embedding_function=ef,  # type: ignore
)


def extract_text_from_pdf(file_obj) -> str:
    try:
        render = PdfReader(file_obj)
        full_text = ""

        for page in render.pages:
            full_text += page.extract_text() or ""

        return full_text

    except Exception as e:
        print(f"Error Reading PDF : {e}")
        return ""


def add_to_chromadb(file_obj, unique_resume_id: str):
    raw_text = extract_text_from_pdf(file_obj)
    if not raw_text:
        return False

    session_id = unique_resume_id.split("||")[0]

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    metadatas = [
        {"session_id": session_id, "resume_id": unique_resume_id} for _ in chunks
    ]

    collection.add(
        documents=chunks,
        metadatas=metadatas,  # type: ignore
        ids=[f"{unique_resume_id}_chunk_{i}" for i in range(len(chunks))],
    )

    return True


def analyze_resume(job_description: str, unique_resume_id: str) -> Resume:
    results = collection.query(
        query_texts=[job_description],
        n_results=5,
        where={"resume_id": unique_resume_id},
    )

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
