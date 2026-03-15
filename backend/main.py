from fastapi import FastAPI

app = FastAPI(title="Indy Explorer API")


@app.get("/health")
def health():
    return {"status": "ok"}
