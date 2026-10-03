import os
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ResearchS API",
    description="AI-powered research paper summarization and question answering system",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
def root():
    return {
        "message": "Welcome to the ResearchS API",
        "status": "Backend is running successfully"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Validate file presence and extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files (.pdf) are allowed."
        )

    # Sanitize filename and create unique storage path to avoid collisions
    original_filename = os.path.basename(file.filename)
    safe_stored_name = f"{uuid.uuid4().hex[:8]}_{original_filename}"
    file_path = UPLOAD_DIR / safe_stored_name

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = file_path.stat().st_size
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded PDF: {str(exc)}"
        )
    finally:
        await file.close()

    return {
        "message": "PDF uploaded and validated successfully.",
        "filename": original_filename,
        "saved_filename": safe_stored_name,
        "file_size_bytes": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "status": "success"
    }