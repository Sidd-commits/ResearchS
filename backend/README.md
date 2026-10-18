# ResearchS ✦ Backend REST API Service

[![API Docs](https://img.shields.io/badge/Swagger%20Docs-Interactive-009688?style=flat-square&logo=fastapi&logoColor=white)](https://researchs-backend.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/Inference-PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)

The core analytical backend for **ResearchS**, powering PDF ingestion, academic text normalization, multi-model transformer summarization, and retrieval-augmented generation (RAG) question answering.

---

## 🌐 Live Service Endpoints

* **Base URL**: [https://researchs-backend.onrender.com](https://researchs-backend.onrender.com)
* **Interactive Swagger UI**: [https://researchs-backend.onrender.com/docs](https://researchs-backend.onrender.com/docs)
* **ReDoc Documentation**: [https://researchs-backend.onrender.com/redoc](https://researchs-backend.onrender.com/redoc)
* **Health Check**: [https://researchs-backend.onrender.com/health](https://researchs-backend.onrender.com/health)

---

## 🏗️ Architecture & Modules

```text
backend/
├── app/
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── model_evaluator.py       # ROUGE-1/2/L calculation & winning model serialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bart.py                  # Meta BART (facebook/bart-large-cnn)
│   │   ├── flan_t5.py               # Google FLAN-T5 (google/flan-t5-base)
│   │   └── long_t5.py               # Google LongT5 (google/long-t5-tglobal-base)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py           # PyMuPDF text extraction, cleaning, and chunking
│   │   ├── qa_service.py            # TF-IDF sparse retrieval & grounded FLAN-T5 chatbot
│   │   └── summarization_service.py # Multi-model pipeline orchestration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── env_utils.py             # Memory-aware cloud vs. local environment detection
│   └── main.py                      # FastAPI application entrypoint, CORS & route definitions
├── uploads/                         # Temporary PDF workspace (.gitkeep tracked)
├── best_model.pkl                   # Winning model metadata checkpoint
└── requirements.txt                 # Pinned dependencies with CPU wheel index
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Uptime check and service version verification |
| `GET` | `/sample-paper` | Loads or dynamically generates a benchmark scientific PDF |
| `GET` | `/search-arxiv?query={term}` | Searches arXiv academic database with resilient fallback |
| `POST` | `/import-arxiv-paper` | Compiles arXiv metadata into a PDF and runs preprocessing |
| `POST` | `/upload-pdf` | Accepts an academic PDF upload, extracts, cleans, and chunks |
| `POST` | `/papers/{filename}/summarize` | Generates summary via `flan-t5`, `bart`, or `long-t5` |
| `POST` | `/papers/{filename}/compare` | Evaluates all 3 models side-by-side; writes `best_model.pkl` |
| `POST` | `/papers/{filename}/chat` | Contextual RAG question answering with chunk citations |
| `GET` | `/best-model` | Retrieves winning model evaluation metadata |

---

## ⚙️ Environment Adaptation

The backend features intelligent hardware detection ([`app/utils/env_utils.py`](app/utils/env_utils.py)):
* **Cloud Environments (e.g., Render Free Tier 512MB RAM)**:
  * Activates fast, grounded semantic summarization and RAG Q&A (< 30MB RAM, < 0.2s latency) to avoid OOM SIGKILL (exit code 137).
  * Computes genuine ROUGE-1, ROUGE-2, and ROUGE-L scores using `model_evaluator`.
  * Serializes `best_model.pkl`.
* **Local Workstations (NVIDIA GPU / High RAM)**:
  * Automatically loads full pretrained Hugging Face transformer weights with CUDA acceleration.

---

## 🚀 Local Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access Swagger UI at `http://localhost:8000/docs`.

---

## 📄 License

This project is licensed under the [MIT License](../LICENSE).
