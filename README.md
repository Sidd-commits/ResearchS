# ResearchS ✦ AI-Powered Research Assistant

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=flat-square&logo=react)](https://vitejs.dev)
[![Hugging Face](https://img.shields.io/badge/Models-Hugging%20Face%20Transformers-FFD21E?style=flat-square&logo=huggingface)](https://huggingface.co)
[![PyTorch CUDA](https://img.shields.io/badge/Acceleration-PyTorch%20CUDA%2012.1-EE4C2C?style=flat-square&logo=pytorch)](https://pytorch.org)
[![License](https://img.shields.io/badge/License-Academic-blue?style=flat-square)](docs/SHOWCASE_AND_VIVA_GUIDE.md)

**ResearchS** is an end-to-end NLP research paper analysis, summarization, and comparative evaluation system. It allows researchers and students to search peer-reviewed papers on **arXiv**, upload academic PDFs, preprocess and clean scientific discourse, run abstractive inference across pretrained transformer models, and benchmark results using standardized **ROUGE** metrics.

---


## 🌟 Key Features

* **Real-Time arXiv Search**: Query arXiv directly by keyword or paper title; preview metadata and seamlessly import full academic papers for analysis.
* **PDF Ingestion & Validation**: Secure PDF upload with UUID sanitization and file integrity validation via FastAPI.
* **Academic NLP Preprocessing**:
  * Primary extraction via C-optimized **PyMuPDF** (`pymupdf`) with **PyPDF** fallback.
  * Regex ligature and hyphenation repair (`trans-\nformer` $\rightarrow$ `transformer`).
  * Citation bracket stripping (`[1]`, `[2, 3]`) and header/footer normalization.
  * Sentence-aware sliding-window chunking (`[.!?]\s+`) with configurable overlap.
* **Pretrained Transformer Inference**:
  * **Google FLAN-T5** (`google/flan-t5-base`, 250M parameters) — Instruction Seq2Seq.
  * **Meta BART** (`facebook/bart-large-cnn`, 406M parameters) — Denoising Autoencoder Seq2Seq.
  * **Google LongT5** (`google/long-t5-tglobal-base`, 250M parameters) — Transient Global long-context (4096 tokens).
* **Interactive PDF Research Chatbot (Step 26 & Features 9/10)**:
  * Context-aware Question Answering grounded in academic sentence chunks.
  * Fast TF-IDF chunk retrieval + zero-shot generation using Google FLAN-T5.
  * Displays cited chunks, similarity confidence scores, and preview snippets.
* **Empirical Benchmarking & Scoring**:
  * Unigram overlap (**ROUGE-1 F1**).
  * Bigram phrasing fluency (**ROUGE-2 F1**).
  * Longest Common Subsequence structure (**ROUGE-L F1**).
  * Inference latency in seconds and generation tokens/sec.
* **Serialized Model Checkpoint (Rubric Criterion 14)**:
  * Automatically serializes the winning model architecture, parameters, and benchmark scores to `backend/best_model.pkl`.
* **Hardware-Safe Lifecycle**:
  * Sequential model execution with explicit VRAM purging (`torch.cuda.empty_cache()` and `gc.collect()`), maintaining peak GPU memory strictly under **1.6 GB** (tested on NVIDIA RTX 2050 4GB).

---

## 🏗️ System Architecture

```text
React Frontend (Vite)
       ↓  (HTTP REST / JSON / Multipart)
FastAPI Backend
       ↓
Preprocessing Engine (PyMuPDF: extract → clean citations → sentence chunking)
       ↓
Hugging Face Transformers (Sequential CUDA execution: FLAN-T5 & BART)
       ↓
Evaluation Engine (ROUGE-1, ROUGE-2, ROUGE-L, Latency Benchmarking)
       ↓
Persistence (best_model.pkl checkpoint artifact) & Interactive Dashboard
```

Detailed technical specifications and hardware safety constraints are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📂 Project Structure

```text
ResearchS/
├── backend/
│   ├── app/
│   │   ├── evaluation/
│   │   │   └── model_evaluator.py     # ROUGE-1/2/L scoring & .pkl serialization
│   │   ├── models/
│   │   │   ├── bart.py                # Meta BART wrapper (facebook/bart-large-cnn)
│   │   │   ├── flan_t5.py             # Google FLAN-T5 wrapper (google/flan-t5-base)
│   │   │   └── long_t5.py             # Google LongT5 wrapper (google/long-t5-tglobal-base)
│   │   ├── services/
│   │   │   ├── pdf_service.py         # PyMuPDF extraction, cleaning, chunking
│   │   │   ├── qa_service.py          # TF-IDF RAG & FLAN-T5 Paper Chatbot
│   │   │   └── summarization_service.py # Comparative pipeline orchestrator
│   │   └── main.py                    # FastAPI routes, arXiv integration, Chatbot Q&A
│   ├── uploads/                       # PDF uploads (gitignored for privacy)
│   ├── best_model.pkl                 # Serialized winning model checkpoint artifact
│   └── requirements.txt               # Pinned Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Interactive dashboard component
│   │   ├── index.css                  # Responsive design system
│   │   └── main.jsx                   # React root entry
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── ARCHITECTURE.md                # System design & memory safety specifications
│   ├── SHOWCASE_AND_VIVA_GUIDE.md     # 14-point academic rubric & viva answers
│   └── PROJECT_CONTEXT.md             # Project roadmap and historical milestones
├── .gitignore                         # Strict leak-prevention rules (uploads, .env, venv)
└── README.md                          # Repository documentation
```

---

## 🚀 Getting Started

### 1. Backend Setup (FastAPI & PyTorch)

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

* API server: `http://127.0.0.1:8000`
* Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup (React & Vite)

```bash
cd frontend
npm install
npm run dev
```

* User interface: `http://localhost:5173`

---

## 📖 Documentation & Evaluation

* **[SHOWCASE_AND_VIVA_GUIDE.md](docs/SHOWCASE_AND_VIVA_GUIDE.md)**: Comprehensive answers to all 14 viva questions, base paper comparison, ROUGE metric definitions, and Hugging Face verification details.
* **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Hardware constraints, sequential GPU memory unloading, and pipeline specifications.
* **[PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)**: Chronological development roadmap and milestone tracking.

---

## 🔒 Security & Privacy

* No API keys, credentials, or personal access tokens are committed or stored in this repository.
* User-uploaded documents and temporary files in `backend/uploads/` are excluded via `.gitignore`.
* Virtual environments, local caches, and build artifacts are strictly ignored.

---

## 👥 Authors
Developed for the NLP Project Research Showcase.
