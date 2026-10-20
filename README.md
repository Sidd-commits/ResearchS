# ResearchS ✦ AI-Powered Academic Research Assistant

[![Live App](https://img.shields.io/badge/Live%20App-Render%20Cloud-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://researchs-frontend.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger%20UI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://researchs-backend.onrender.com/docs)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://researchs-frontend.onrender.com)
[![Models](https://img.shields.io/badge/Models-Hugging%20Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

> **ResearchS** is an end-to-end, full-stack NLP research platform for scientific paper discovery, automated abstractive summarization, multi-model transformer benchmarking, and citation-grounded conversational question answering (RAG).


---

## 🌐 Live Cloud Deployment

The application is deployed and actively running on **Render Cloud Infrastructure**:

| Component | Status | Live URL | Description |
| :--- | :---: | :--- | :--- |
| **Frontend Web App** | ![Active](https://img.shields.io/badge/Status-Online-brightgreen?style=flat-square) | **[researchs-frontend.onrender.com](https://researchs-frontend.onrender.com)** | Responsive React 19 + Vite research workspace |
| **Backend REST API** | ![Active](https://img.shields.io/badge/Status-Online-brightgreen?style=flat-square) | **[researchs-backend.onrender.com](https://researchs-backend.onrender.com)** | High-throughput FastAPI engine |
| **Interactive API Docs** | ![Active](https://img.shields.io/badge/Swagger-Interactive-blue?style=flat-square) | **[researchs-backend.onrender.com/docs](https://researchs-backend.onrender.com/docs)** | OpenAPI / Swagger interactive documentation |
| **Health Monitoring** | ![Healthy](https://img.shields.io/badge/Health-200%20OK-success?style=flat-square) | **[researchs-backend.onrender.com/health](https://researchs-backend.onrender.com/health)** | Uptime probe and container lifecycle check |

---

## 🌟 Key Capabilities

* **Real-Time arXiv Search & Instant Paper Ingestion**:
  * Direct querying against arXiv API (`export.arxiv.org`) with automated title, abstract, and author parsing.
  * Resilient fallback cache providing instant access to foundational AI papers (*Attention Is All You Need*, *BART*, *BERT*, *LongT5*).
  * One-click ingestion that compiles paper metadata into structured academic PDFs.
* **Academic PDF Extraction & Cleaning Pipeline**:
  * High-throughput text extraction powered by C-optimized **PyMuPDF** (`fitz`) with fallback to **PyPDF**.
  * De-hyphenation across line breaks (e.g., `trans-\nformer` $\rightarrow$ `transformer`) and Unicode ligature repair (`fi`, `fl`).
  * In-text citation bracket removal (`[1]`, `[2, 3]`) and header/footer normalization.
  * Sentence-boundary sliding window chunking (`[.!?]\s+`) with configurable token overlap for contextual continuity.
* **Multi-Model Transformer Inference**:
  * **Google FLAN-T5** (`google/flan-t5-base`, ~250M params) — Instruction-tuned Seq2Seq model optimized for factual, concise synthesis.
  * **Meta BART** (`facebook/bart-large-cnn`, ~406M params) — Denoising autoencoder Seq2Seq model producing fluid, coherent narratives.
  * **Google LongT5** (`google/long-t5-tglobal-base`, ~250M params) — Transient Global Attention scaling input context to 4,096 tokens for long-document modeling.
* **Comparative Evaluation & Benchmark Matrix**:
  * Automated side-by-side model comparison on the exact same research paper.
  * Evaluated on unigram recall (**ROUGE-1 F1**), bigram fluency (**ROUGE-2 F1**), and longest common subsequence (**ROUGE-L F1**).
  * Latency tracking (execution seconds and tokens per second).
  * Automated model selection and artifact serialization (`backend/best_model.pkl`).
* **Citation-Grounded RAG Chatbot**:
  * Context-aware Question Answering over uploaded paper chunks.
  * TF-IDF sparse similarity scoring paired with zero-shot synthesis via Google FLAN-T5.
  * Transparent citation tracking showing retrieved chunk snippets, chunk indices, and similarity confidence scores.
* **Dual-Environment Architecture (Cloud vs. Localhost)**:
  * Automatically detects constrained cloud environments (Render Free Tier 512MB RAM ceiling) to eliminate Out-Of-Memory (OOM) SIGKILL failures.
  * Executes full PyTorch CUDA GPU inference when run locally with sufficient hardware.


---

## 🏗️ Architecture & Data Flow


```text
                     ┌──────────────────────────────────────────────┐
                     │          React 19 Frontend (Vite)            │
                     │    https://researchs-frontend.onrender.com   │
                     └──────────────────────┬───────────────────────┘
                                            │ HTTP / JSON / Multipart
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │          FastAPI Backend Gateway             │
                     │    https://researchs-backend.onrender.com    │
                     └──────┬───────────────┬────────────────┬──────┘
                            │               │                │
            ┌───────────────┴────┐   ┌──────┴─────────┐   ┌──┴──────────────────┐
            │ Preprocessing      │   │ Model Hub      │   │ RAG Engine          │
            ├────────────────────┤   ├────────────────┤   ├─────────────────────┤
            │ • PyMuPDF / fitz   │   │ • FLAN-T5 Base │   │ • TF-IDF Vectorizer │
            │ • Ligature Repair  │   │ • BART Large   │   │ • Cosine Similarity │
            │ • De-hyphenation   │   │ • LongT5       │   │ • Grounded Q&A      │
            │ • Sentence Chunks  │   │ • ROUGE-1/2/L  │   │ • Chunk Citations   │
            └────────────────────┘   └────────────────┘   └─────────────────────┘
```

---

## 📡 Live API Endpoints Reference

All endpoints are live and accessible via HTTPS:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and uptime probe |
| `GET` | `/sample-paper` | Generates / loads benchmark sample research paper |
| `GET` | `/search-arxiv?query={term}` | Searches arXiv academic repository |
| `POST` | `/import-arxiv-paper` | Imports an arXiv paper, generates PDF, and preprocesses text |
| `POST` | `/upload-pdf` | Uploads an academic PDF, extracts, cleans, and chunks text |
| `POST` | `/papers/{filename}/summarize` | Generates summary using specified model (`flan-t5`, `bart`, `long-t5`) |
| `POST` | `/papers/{filename}/compare` | Runs 3-model benchmark comparison and saves `best_model.pkl` |
| `POST` | `/papers/{filename}/chat` | RAG Q&A chatbot query grounded in paper context |
| `GET` | `/best-model` | Retrieves serialized winning model benchmark metadata |

### Quick Example: Querying the Live API with curl

```bash
# 1. Check Backend Health
curl -s https://researchs-backend.onrender.com/health

# 2. Search arXiv for Research Papers
curl -s "https://researchs-backend.onrender.com/search-arxiv?query=attention"

# 3. Load Sample Research Paper
curl -s https://researchs-backend.onrender.com/sample-paper
```

---

## 📂 Repository Structure

```text
ResearchS/
├── .gitignore                         # Strict exclusion rules (no keys, docs, or PDFs)
├── LICENSE                            # MIT License
├── README.md                          # Main repository documentation & live links
├── render.yaml                        # Infrastructure-as-Code Blueprint for Render
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
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── env_utils.py           # Cloud vs. local environment detection
│   │   └── main.py                    # FastAPI entrypoint, routes, and CORS setup
│   ├── uploads/
│   │   └── .gitkeep                   # Tracks folder structure without committing PDFs
│   ├── best_model.pkl                 # Winning model checkpoint metadata
│   ├── requirements.txt               # Pinned Python dependencies
│   └── README.md                      # Backend service documentation
└── frontend/
    ├── public/
    │   ├── apple-touch-icon.png       # 180x180 iOS touch icon
    │   ├── favicon.svg                # Brand icon
    │   ├── icons.svg                  # SVG sprite icons
    │   ├── manifest.json              # Web App Manifest
    │   ├── og-image.png               # 1200x630 Open Graph social preview banner
    │   ├── robots.txt                 # Search crawler directives
    │   └── sitemap.xml                # Canonical XML sitemap
    ├── src/
    │   ├── App.jsx                    # Reactive research dashboard component
    │   ├── index.css                  # Responsive minimalist design system
    │   └── main.jsx                   # React root mount
    ├── .gitignore
    ├── eslint.config.js
    ├── index.html                     # Page metadata & title
    ├── package.json                   # Dependencies and build scripts
    ├── package-lock.json
    ├── vite.config.js
    └── README.md                      # Frontend documentation
```

---

## 🚀 Local Development Setup

To run ResearchS on your local workstation with full GPU hardware acceleration:

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
* Interactive Documentation: `http://localhost:8000/docs`

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

## ☁️ Deployment on Render

This repository includes a [`render.yaml`](render.yaml) Blueprint configured for zero-downtime continuous deployment:

1. **Backend Web Service (`researchs-backend`)**:
   * Runtime: Python 3.11
   * Build: `pip install -r requirements.txt` (using optimized CPU PyTorch wheels)
   * Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * Automatic continuous deployment on push to `main` branch.

2. **Frontend Static Site (`researchs-frontend`)**:
   * Runtime: Static Site
   * Build: `npm ci && npm run build`
   * Publish Path: `dist`
   * Automatic rewrite rules routing to `/index.html`.

---

## 🔒 Security & Privacy

* **Zero Credentials**: No API keys, passwords, or personal credentials are stored in this repository.
* **Strict Exclusions**: All uploaded academic documents, local virtual environments, OS caches, and internal artifacts are excluded via `.gitignore`.
* **Sanitized Filenames**: Uploaded documents are assigned randomized UUIDs to prevent directory traversal or file collisions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
