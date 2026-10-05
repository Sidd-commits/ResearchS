import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.services.pdf_service import pdf_service, PDFPreprocessingError

logger = logging.getLogger("researchs.api")

app = FastAPI(
    title="ResearchS API",
    description="AI-powered research paper summarization, comparison, and question answering system",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite) — supports both local dev and production
_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
_allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if _frontend_url:
    _allowed_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
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


class ArxivImportRequest(BaseModel):
    title: str
    summary: str
    authors: Optional[List[str]] = []
    published: Optional[str] = ""
    arxiv_id: Optional[str] = ""

@app.post("/import-arxiv-paper")
def import_arxiv_paper(req: ArxivImportRequest):
    """
    Imports an arXiv paper found via search:
    Generates a structured research PDF containing title, authors,
    publication date, arXiv citation reference, and full abstract,
    then executes the preprocessing pipeline (text extraction, cleaning, chunking).
    """
    import pymupdf

    safe_title_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", req.title.strip())[:30].strip("_")
    unique_prefix = uuid.uuid4().hex[:8]
    safe_stored_name = f"arxiv_{unique_prefix}_{safe_title_slug}.pdf"
    file_path = UPLOAD_DIR / safe_stored_name

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    page.insert_text((50, 45), f"arXiv Pre-print: {req.arxiv_id or 'arXiv.org'}", fontsize=9, color=(0.4, 0.4, 0.5))

    rect_title = pymupdf.Rect(50, 65, 545, 140)
    page.insert_textbox(rect_title, req.title, fontsize=15, fontname="helv", color=(0.1, 0.1, 0.15))

    authors_str = ", ".join(req.authors) if req.authors else "Anonymous"
    pub_str = f"Authors: {authors_str}  |  Published: {req.published or 'Recent'}"
    page.insert_text((50, 150), pub_str, fontsize=9.5, color=(0.3, 0.3, 0.4))

    page.insert_text((50, 185), "Abstract & Key Methodology:", fontsize=12, fontname="helv", color=(0.15, 0.15, 0.2))

    rect_abstract = pymupdf.Rect(50, 205, 545, 780)
    page.insert_textbox(rect_abstract, req.summary, fontsize=10.5, fontname="helv", color=(0.2, 0.2, 0.25))

    doc.save(str(file_path))
    doc.close()

    preprocessing = pdf_service.process_pdf(file_path)

    return {
        "message": f"arXiv paper '{req.title}' successfully imported and preprocessed.",
        "filename": f"{req.title[:45]} (arXiv).pdf",
        "saved_filename": safe_stored_name,
        "file_size_bytes": file_path.stat().st_size,
        "file_size_kb": round(file_path.stat().st_size / 1024, 2),
        "status": "success",
        "preprocessing": preprocessing,
    }


class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3


@app.post("/papers/{saved_filename}/chat")
def chat_with_paper(saved_filename: str, req: ChatRequest):
    """
    Step 26: PDF-Based Interactive Research Paper Chatbot (Q&A).
    Retrieves context-relevant chunks via TF-IDF and generates
    grounded answers using Google FLAN-T5.
    """
    from app.services.qa_service import qa_service

    try:
        result = qa_service.answer_question(
            saved_filename=saved_filename,
            question=req.question,
            top_k=req.top_k or 3,
        )
        return result
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(exc)}")


@app.post("/papers/{saved_filename}/summarize")
def summarize_paper(
    saved_filename: str,
    model_type: str = Query(default="flan-t5", description="Model: 'flan-t5', 'bart', or 'long-t5'"),
    max_length: int = Query(default=160, ge=40, le=512),
    min_length: int = Query(default=40, ge=10, le=200),
):
    """
    Step 19 (FLAN-T5), Step 20 (BART), Step 21 (LongT5):
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

