from fastapi import FastAPI

app = FastAPI(title="InvoiceFlow")

@app.get("/health")
def health():
    return {"status": "ok"}