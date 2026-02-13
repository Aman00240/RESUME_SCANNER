import uuid
from fastapi import APIRouter, HTTPException, File, UploadFile
from backend.modules.rag import add_to_chromadb, analyze_resume, collection
from backend.schemas import JobQuery, BatchAnalysisResponse, ChatQuery, ChatResponse
from backend.modules.rag import chat_with_resume_ai

router = APIRouter()


@router.post("/upload")
def upload_resume(files: list[UploadFile] = File(...)):
    try:
        batch_id = str(uuid.uuid4())
        uploaded_count = 0

        for file in files:
            unique_resume_id = f"{batch_id}||{file.filename}"
            success = add_to_chromadb(file.file, unique_resume_id)
            if success:
                uploaded_count += 1

        if uploaded_count == 0:
            raise HTTPException(status_code=400, detail="Failed to process any files")

        return {"message": "Success", "batch_id": batch_id, "count": uploaded_count}

    except Exception as e:
        print(f"Upload Eror: {e}")
        raise HTTPException(status_code=500, detail="Internal server Error")


@router.post("/analyze", response_model=BatchAnalysisResponse)
def analyze_resume_endpoint(job_query: JobQuery):
    try:
        existing_data = collection.get(where={"session_id": job_query.session_id})

        if not existing_data or not existing_data["ids"]:
            raise HTTPException(
                status_code=404, detail="No resume found for this session"
            )

        unique_files = set()

        current_metadatas = existing_data.get("metadatas") or []

        for meta in current_metadatas:
            if "resume_id" in meta:
                unique_files.add(meta["resume_id"])

        results_list = []

        for resume_id in unique_files:
            filename = resume_id.split("||")[1]

            try:
                analysis_obj = analyze_resume(job_query.job_description, resume_id)

                results_list.append({"filename": filename, "analysis": analysis_obj})

            except Exception as inner_e:
                print(f"Skipping {filename} due to error: {inner_e}")
                continue

        results_list.sort(key=lambda x: x["analysis"].match_score, reverse=True)

        return {"results": results_list}

    except Exception as e:
        print(f"Batch Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
def chat(query: ChatQuery):
    try:
        jd = query.job_description or ""

        answer = chat_with_resume_ai(query.question, query.resume_id, jd)
        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
