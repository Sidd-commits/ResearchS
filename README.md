# ResearchS ✦ AI-Powered Research Assistant

**ResearchS** is an end-to-end NLP research paper summarization, comparison, and question-answering system. It allows researchers and students to upload research-paper PDFs or query arXiv, extract and preprocess text, run inference across multiple pretrained transformer models, and interact with the paper via an intelligent chatbot.

---

## 🌟 Key Features

- **PDF Ingestion & Validation**: Fast, secure upload of research papers with FastAPI.
- **NLP Preprocessing**: Robust text extraction with PyMuPDF/PyPDF, regex cleaning, and recursive token-aware chunking.
- **Transformer-based Summarization**:
  - **Google FLAN-T5** (`google/flan-t5-base`)
  - **Meta BART** (`facebook/bart-large-cnn`)
  - **LongT5** (`google/long-t5-tglobal-base`)
  - **Mistral 7B** (Quantized / API inference)
- **Model Benchmarking & Evaluation**: Side-by-side comparison of summaries with ROUGE-1, ROUGE-2, ROUGE-L, and inference latency.
- **Research Chatbot**: Context-aware Q&A on paper contents.
- **Modern Dashboard**: Sleek, responsive React frontend powered by Vite.

---

## 🏗️ System Architecture

```text
React Frontend (Vite)
       ↓  (HTTP / REST API)
FastAPI Backend
       ↓
PDF Processing & Chunking (PyMuPDF / PyPDF)
       ↓
Pretrained Transformer Models (FLAN-T5, BART, LongT5, Mistral)
       ↓
Evaluation & Model Comparison (ROUGE, Latency)
       ↓
Interactive Research Chatbot & Visual Dashboard
```

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend runs at `http://127.0.0.1:8000`  
Interactive Swagger API docs at `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

---

## 📂 Project Structure

```text
ResearchS/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── uploads/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── PROJECT_CONTEXT.md
├── AGENTS.md
└── README.md
```

---

## 👥 Authors
Developed for NLP Project Research Showcase.
