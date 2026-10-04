# ResearchS — System Architecture & Engineering Specifications

This document outlines the architectural design, data flow, memory lifecycle management, and hardware safety strategies employed in **ResearchS**.

---

## 1. High-Level Architectural Diagram

```
+--------------------------------------------------------------------------+
|                        REACT FRONTEND (Vite / CSS)                       |
|   • arXiv Real-time Search     • PDF Drag & Drop Ingestion               |
|   • Dual-Model Benchmarking    • Single-Model Abstractive Summarizer     |
+------------------------------------+-------------------------------------+
                                     | HTTP REST (JSON / Multipart)
                                     v
+--------------------------------------------------------------------------+
|                         FASTAPI BACKEND SERVICE                          |
|  [POST /upload-pdf]          [POST /import-arxiv-paper]                  |
|  [GET  /search-arxiv]        [GET  /sample-paper]                        |
|  [POST /papers/{id}/compare] [POST /papers/{id}/summarize]               |
|  [POST /papers/{id}/chat]    [GET  /best-model]                          |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                     PREPROCESSING & RETRIEVAL PIPELINE                   |
|  1. Text Extraction (PyMuPDF / C-bindings with PyPDF fallback)           |
|  2. Academic De-noising (Regex ligature repair, citation normalization)   |
|  3. Sentence-Aware Sliding Window Chunking (overlap = 200 chars)         |
|  4. TF-IDF Chunk Ranking & Dense Query Matching for RAG Q&A              |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                 HUGGING FACE MODEL RUNTIME (PyTorch CUDA)                |
|  • Model A: Google FLAN-T5 (google/flan-t5-base) — Factual & Q&A RAG     |
|  • Model B: Meta BART (facebook/bart-large-cnn) — Deep Abstractive       |
|  • Model C: Google LongT5 (google/long-t5-tglobal-base) — 4096 TGlobal   |
|  • Sequential Execution & Memory Unloading:                              |
|      load -> infer -> unload -> torch.cuda.empty_cache() -> gc.collect()  |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                     EVALUATION & ARTIFACT PERSISTENCE                    |
|  • ROUGE-1 (Unigram Informativeness)                                     |
|  • ROUGE-2 (Bigram Terminology Fluency)                                  |
|  • ROUGE-L (Longest Common Subsequence Order)                            |
|  • Latency Benchmark (seconds / tokens per sec)                          |
|  • Serialized Best Model Artifact: backend/best_model.pkl (Criterion 14) |
+--------------------------------------------------------------------------+
```

---

## 2. Hardware Safety & Memory Optimization Strategy

ResearchS is engineered to run safely on entry-level GPU hardware (e.g. **NVIDIA GeForce RTX 2050 with 4 GB VRAM** and **8 GB System RAM**) without risking out-of-memory errors, system thrashing, or thermal degradation.

### Key Memory Guarantees:
1. **Sequential Loading (No Concurrent Model Footprint)**:
   - During side-by-side comparison, FLAN-T5 is loaded into VRAM, generates its summary, and is **immediately unloaded** (`del model`, `del tokenizer`, `gc.collect()`, `torch.cuda.empty_cache()`).
   - Only after VRAM is freed is Meta BART loaded into VRAM.
   - Peak VRAM consumption stays strictly **under 1.6 GB**, well within the 4 GB hardware ceiling.
2. **C-Optimized PDF Extraction**:
   - PyMuPDF reads document streams in fast native C memory without loading uncompressed page bitmaps into RAM.
3. **Chunking Bounds**:
   - Sentence-aware chunks are capped at 1,200 characters with 200-character overlap, strictly fitting within transformer sequence lengths (max 1024 tokens) to prevent quadratic attention memory blowup.

---

## 3. Project Directory Hierarchy

```
ResearchS/
├── backend/
│   ├── app/
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   └── model_evaluator.py     # ROUGE-1/2/L & .pkl serialization
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── bart.py                # Meta BART (facebook/bart-large-cnn)
│   │   │   ├── flan_t5.py             # Google FLAN-T5 (google/flan-t5-base)
│   │   │   └── long_t5.py             # Google LongT5 (google/long-t5-tglobal-base)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_service.py         # PyMuPDF extraction, cleaning & chunking
│   │   │   ├── qa_service.py          # TF-IDF RAG & FLAN-T5 Paper Chatbot
│   │   │   └── summarization_service.py # Orchestrator for inference
│   │   └── main.py                    # FastAPI routes, CORS, arXiv import, Chatbot Q&A
│   ├── uploads/                       # Temporary storage (gitignored)
│   ├── best_model.pkl                 # Evaluated winning model checkpoint
│   └── requirements.txt               # Pinned dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Reactive UI dashboard
│   │   ├── main.jsx                   # React root entry
│   │   └── index.css                  # Modern responsive design system
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── ARCHITECTURE.md                # System design & hardware specs (this file)
│   ├── SHOWCASE_AND_VIVA_GUIDE.md     # 14-point academic rubric & viva answers
│   └── PROJECT_CONTEXT.md             # Historical roadmap and evolution
├── .gitignore                         # Strict leak-prevention rules
└── README.md                          # Primary project showcase & quickstart
```
