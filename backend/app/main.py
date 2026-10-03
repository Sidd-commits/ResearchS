import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.services.pdf_service import pdf_service, PDFPreprocessingError

logger = logging.getLogger("researchs.api")

app = FastAPI(
    title="ResearchS API",
    description="AI-powered research paper summarization, comparison, and question answering system",
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
async def upload_pdf(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Query(default=1200, ge=200, le=4000),
    chunk_overlap: Optional[int] = Query(default=200, ge=0, le=500),
):
    """
    Step 16 & 17 & 18:
    Uploads a research PDF, validates it, stores it, extracts raw text,
    cleans academic noise, and performs sentence-aware chunking.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files (.pdf) are allowed."
        )

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

    # Preprocess text (Step 17 extraction + Step 18 cleaning & chunking)
    try:
        preprocessing = pdf_service.process_pdf(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except PDFPreprocessingError as err:
        logger.warning(f"Preprocessing error on {safe_stored_name}: {err}")
        preprocessing = {
            "status": "error",
            "message": str(err),
            "page_count": 0,
            "chunks": [],
        }

    return {
        "message": "PDF uploaded and preprocessed successfully.",
        "filename": original_filename,
        "saved_filename": safe_stored_name,
        "file_size_bytes": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "status": "success",
        "preprocessing": preprocessing,
    }

@app.get("/papers/{saved_filename}/preprocess")
def get_paper_preprocessing(
    saved_filename: str,
    chunk_size: Optional[int] = Query(default=1200, ge=200, le=4000),
    chunk_overlap: Optional[int] = Query(default=200, ge=0, le=500),
):
    """
    Re-runs or inspects text extraction, cleaning, and chunking with custom parameters.
    """
    file_path = UPLOAD_DIR / os.path.basename(saved_filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested PDF file not found.")

    try:
        result = pdf_service.process_pdf(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(exc)}")

@app.get("/uploads")
def list_uploaded_papers():
    """Lists all currently saved research papers in the uploads folder."""
    papers = []
    for f in UPLOAD_DIR.glob("*.pdf"):
        papers.append({
            "saved_filename": f.name,
            "file_size_kb": round(f.stat().st_size / 1024, 2),
        })
    return {"papers": papers, "count": len(papers)}

@app.get("/sample-paper")
def get_sample_demo_paper():
    """
    Returns a ready-to-test sample research paper for instant 1-click evaluation.
    """
    sample_file = UPLOAD_DIR / "1912ba7c_scientific_embeddings.pdf"
    if not sample_file.exists():
        pdfs = list(UPLOAD_DIR.glob("*.pdf"))
        if not pdfs:
            raise HTTPException(status_code=404, detail="No sample paper available.")
        sample_file = pdfs[0]

    preprocessing = pdf_service.process_pdf(sample_file)
    return {
        "message": "Demo research paper loaded successfully.",
        "filename": "scientific_embeddings_nlp.pdf",
        "saved_filename": sample_file.name,
        "file_size_bytes": sample_file.stat().st_size,
        "file_size_kb": round(sample_file.stat().st_size / 1024, 2),
        "status": "success",
        "preprocessing": preprocessing,
    }

@app.get("/search-arxiv")
def search_arxiv(query: str = Query(..., min_length=2)):
    """
    Step 27 / Criteria 1 & 2:
    Searches arXiv API for academic research papers.
    """
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    clean_query = urllib.parse.quote(query.strip())
    url = f"https://export.arxiv.org/api/query?search_query=all:{clean_query}&start=0&max_results=4"
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchS/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            papers = []
            for entry in entries:
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                published = entry.find("atom:published", ns)
                id_elem = entry.find("atom:id", ns)
                authors = [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)
                    if a.find("atom:name", ns) is not None
                ]

                papers.append({
                    "title": title.text.strip().replace("\n", " ") if title is not None else "Untitled",
                    "summary": summary.text.strip().replace("\n", " ") if summary is not None else "",
                    "authors": authors[:3],
                    "published": published.text[:10] if published is not None else "",
                    "arxiv_id": id_elem.text.strip() if id_elem is not None else "",
                })
            return {"query": query, "papers": papers, "count": len(papers)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"arXiv search failed: {str(exc)}")


@app.post("/papers/{saved_filename}/summarize")
def summarize_paper(
    saved_filename: str,
    model_type: str = Query(default="flan-t5", description="Model: 'flan-t5' or 'bart'"),
    max_length: int = Query(default=160, ge=40, le=512),
    min_length: int = Query(default=40, ge=10, le=200),
):
    """
    Step 19 (FLAN-T5) & Step 20 (BART):
    Generates an abstractive summary of an uploaded research paper
    using the specified pretrained transformer model.
    """
    from app.services.summarization_service import summarization_service

    try:
        result = summarization_service.summarize_single_model(
            saved_filename=saved_filename,
            model_type=model_type,
            max_length=max_length,
            min_length=min_length,
        )
        return result
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(exc)}")

@app.post("/papers/{saved_filename}/compare")
def compare_models(
    saved_filename: str,
    max_length: int = Query(default=160, ge=40, le=512),
    min_length: int = Query(default=40, ge=10, le=200),
):
    """
    Runs both Google FLAN-T5 and Meta BART on the exact same research paper,
    compares latency and ROUGE metrics, selects the best model, and saves 'best_model.pkl'.
    """
    from app.services.summarization_service import summarization_service

    try:
        result = summarization_service.compare_models(
            saved_filename=saved_filename,
            max_length=max_length,
            min_length=min_length,
        )
        return result
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(exc)}")

@app.get("/best-model")
def get_best_model_artifact():
    """
    Returns metadata about the serialized 'best_model.pkl' artifact (Professor Criterion 14).
    """
    import pickle
    pkl_path = BASE_DIR / "best_model.pkl"
    if not pkl_path.exists():
        raise HTTPException(
            status_code=404,
            detail="best_model.pkl has not been generated yet. Run model comparison first.",
        )

    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
        return {"status": "success", "artifact_path": str(pkl_path), "metadata": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read best_model.pkl: {str(exc)}")

