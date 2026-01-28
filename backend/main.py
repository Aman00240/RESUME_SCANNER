from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "OK", "message": "API is active"}
