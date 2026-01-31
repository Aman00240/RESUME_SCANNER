from fastapi import FastAPI
from backend.routers import analyze

app = FastAPI()

app.include_router(analyze.router, prefix="/api", tags=["Resume"])


@app.get("/")
def root():
    return {"status": "OK", "message": "API is active"}
