# ResearchS ✦ AI-Powered Academic Research Assistant

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=flat-square&logo=react)](https://vitejs.dev)
[![Hugging Face](https://img.shields.io/badge/Models-Hugging%20Face%20Transformers-FFD21E?style=flat-square&logo=huggingface)](https://huggingface.co)
[![PyTorch CUDA](https://img.shields.io/badge/Acceleration-PyTorch%20CUDA-EE4C2C?style=flat-square&logo=pytorch)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**ResearchS** is an end-to-end NLP research platform designed for scientific literature analysis, abstractive summarization, comparative model evaluation, and grounded question answering. Researchers and students can discover peer-reviewed papers on **arXiv**, upload academic PDFs, clean and normalize complex academic discourse, run multi-model transformer inference, and benchmark results against standard **ROUGE** metrics.

---

## 🌟 Key Capabilities

* **Direct arXiv Integration**: Search arXiv in real time by keywords, paper title, or author; inspect metadata abstracts and import papers directly into the analytical workspace.
* **Robust PDF Ingestion & Validation**: Secure PDF upload pipeline featuring UUID filename hashing, MIME type verification, and document corruption handling.
* **Academic NLP Preprocessing**:
  * High-throughput extraction via C-optimized **PyMuPDF** (`fitz`) with fallback to **PyPDF**.
  * De-hyphenation across line breaks (e.g. `trans-\nformer` $\rightarrow$ `transformer`) and Unicode ligature repair.
  * In-text citation bracket removal (`[1]`, `[2, 3]`) and header/footer normalization.
  * Sentence-boundary sliding window chunking (`[.!?]\s+`) with configurable overlap for semantic continuity.
* **Comparative Transformer Inference**:
  * **Google FLAN-T5** (`google/flan-t5-base`, 250M parameters) — Instruction-tuned Seq2Seq for structured factual extraction.
  * **Meta BART** (`facebook/bart-large-cnn`, 406M parameters) — Denoising autoencoder Seq2Seq for fluid, narrative summaries.
  * **Google LongT5** (`google/long-t5-tglobal-base`, 250M parameters) — Transient Global Attention scaling input context to 4,096 tokens.
* **Interactive Research Q&A Chatbot (RAG)**:
  * Retrieval-Augmented Generation grounded in extracted paper chunks.
  * TF-IDF sparse similarity scoring paired with zero-shot answer generation using Google FLAN-T5.
  * Transparent citation tracking displaying retrieved chunk snippets and similarity confidence scores.
* **Standardized Evaluation & Benchmarking**:
  * Unigram informativeness (**ROUGE-1 F1**).
  * Bigram syntactic fluency (**ROUGE-2 F1**).
  * Longest Common Subsequence structure (**ROUGE-L F1**).
  * Inference latency tracking (elapsed seconds and tokens per second).
* **Automated Best Model Serialization**:
  * Selects the best performing model based on composite ROUGE metrics and serializes configuration metadata to `backend/best_model.pkl`.
* **Hardware-Conscious Memory Lifecycle**:
  * Sequential model loading and immediate memory purge (`torch.cuda.empty_cache()` and `gc.collect()`) maintaining peak VRAM under 1.6 GB.

---

## 🏗️ Architecture & Data Flow

```text
React Frontend (Vite)
       │  (HTTP REST / JSON / Multipart)
       ▼
FastAPI Backend Gateway
       │
       ├─► Preprocessing Engine (PyMuPDF: text extraction → noise cleaning → sentence chunking)
       │
       ├─► Model Inference Engine (Sequential CUDA execution: FLAN-T5, BART, LongT5)
       │
       ├─► Evaluation Engine (ROUGE-1, ROUGE-2, ROUGE-L & Latency Benchmarks)
       │
       └─► RAG Q&A Engine (TF-IDF retrieval + FLAN-T5 generation with citation grounding)
```

---

## 📂 Project Directory Structure

```text
ResearchS/
├── backend/
│   ├── app/
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   └── model_evaluator.py     # ROUGE metric calculation & model selection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── bart.py                # Meta BART (facebook/bart-large-cnn)
│   │   │   ├── flan_t5.py             # Google FLAN-T5 (google/flan-t5-base)
│   │   │   └── long_t5.py             # Google LongT5 (google/long-t5-tglobal-base)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_service.py         # PyMuPDF extraction, cleaning, and chunking
│   │   │   ├── qa_service.py          # TF-IDF RAG retrieval & FLAN-T5 Chatbot
│   │   │   └── summarization_service.py # Multi-model pipeline orchestration
│   │   └── main.py                    # FastAPI entrypoint, routes, and CORS setup
│   ├── uploads/                       # Ephemeral upload storage (.gitkeep tracked)
│   ├── best_model.pkl                 # Winning model checkpoint metadata
│   └── requirements.txt               # Pinned Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Core reactive dashboard component
│   │   ├── index.css                  # Minimalist responsive design system
│   │   └── main.jsx                   # React application root
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── render.yaml                        # Render Blueprint deployment specification
├── .gitignore                         # Security & leak-prevention rules
├── LICENSE                            # MIT License
└── README.md                          # Repository documentation
```

---

## 🚀 Quickstart Guide

### Prerequisites
* **Python**: 3.10 or 3.11
* **Node.js**: 18+ and npm
* *(Optional)* NVIDIA GPU with CUDA for accelerated model inference

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload --port 8000
```

* API Server: `http://localhost:8000`
* Interactive Documentation (Swagger UI): `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

* Web Dashboard: `http://localhost:5173`

---

## ☁️ Deployment (Render)

This repository includes a [`render.yaml`](render.yaml) Blueprint configured for dual-service deployment:

1. **Backend Web Service**: Python 3.11 environment running FastAPI via `uvicorn`.
2. **Frontend Static Site**: Vite client build published to Render's global CDN.

To deploy via Blueprint:
1. Connect your repository on [Render](https://dashboard.render.com).
2. Select **New +** $\rightarrow$ **Blueprint**.
3. Point to this repository; Render will automatically detect and deploy both services.
4. Set the frontend's `VITE_API_URL` environment variable to your deployed backend URL.

---

## 🔒 Security & Privacy

* **Zero Credentials**: No API keys, passwords, or personal credentials are stored in this repository.
* **Strict Exclusions**: All uploaded academic documents, local virtual environments, OS caches, and internal preparation artifacts are strictly excluded via `.gitignore`.
* **Sanitized Filenames**: Uploaded documents are assigned randomized UUIDs to prevent directory traversal or file collisions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
