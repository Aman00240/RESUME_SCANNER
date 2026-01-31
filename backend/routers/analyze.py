import uuid
from fastapi import APIRouter, HTTPException, File, UploadFile
from backend.modules.rag import add_to_chromadb, analyze_resume
from backend.schemas import Resume, JobQuery

router = APIRouter()


@router.post("/upload")
def upload_resume(file: UploadFile = File(...)):
    try:
        session_id = str(uuid.uuid4())

        success = add_to_chromadb(file.file, session_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed To Read PDF")

        return {"message": "Success", "session_id": session_id}

    except Exception as e:
        print(f"Upload Eror: {e}")
        raise HTTPException(status_code=500, detail="Internal server Error")


@router.post("/analyze", response_model=Resume)
def analyze_resume_endpoint(job_query: JobQuery):
    try:
        result = analyze_resume(
            job_description=job_query.job_description, session_id=job_query.session_id
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal server Error")
