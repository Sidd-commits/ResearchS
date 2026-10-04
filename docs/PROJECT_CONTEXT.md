# ResearchS — Project Context

## 1. Project Overview

**Project Name:** ResearchS

**Purpose:** An AI-powered research assistant for understanding research papers. The intended system allows users to search research papers from arXiv, upload research-paper PDFs, process their content, generate intelligent summaries, compare transformer models, and ask questions about research papers through a context-aware chatbot.

## 2. Current Technology Stack

### Frontend
- React
- JavaScript
- Vite-based frontend
- Main files currently discussed:
  - `frontend/src/App.jsx`
  - `frontend/src/index.css`
  - `frontend/src/main.jsx`

### Backend
- Python
- FastAPI
- Uvicorn
- PDF processing
- Transformer models
- Model comparison
- Question answering

### Planned AI Models
The original plan identifies these models for comparison:
- FLAN-T5
- BART
- LongT5
- Mistral 7B

Important decision: the project should use **pretrained transformer models**, not train all four models from scratch. The intended workflow is to load pretrained models, provide research-paper text, generate summaries/answers, evaluate outputs, compare the models, and select the most suitable model.

## 3. Intended Product Features

The planned ResearchS interface and functionality include:

1. Search research papers using arXiv.
2. Upload research-paper PDFs.
3. Extract and process PDF text.
4. Clean and split research-paper text.
5. Generate intelligent summaries.
6. Compare multiple transformer models.
7. Evaluate model outputs.
8. Select the most suitable model based on evaluation.
9. Ask questions about an uploaded research paper.
10. Provide context-aware chatbot answers.
11. Integrate the backend functionality with the React frontend.

## 4. Frontend Status

### Step 14
The basic React application was confirmed working.

### Step 15 — Completed
A first ResearchS dashboard was created.

The intended dashboard contains:
- Modern navigation bar
- ResearchS branding
- Hero section
- arXiv research-paper search input
- Upload PDF button
- Feature cards
- Responsive layout
- Workflow section

The Step 15 frontend was implemented primarily in:
- `frontend/src/App.jsx`
- `frontend/src/index.css`

`main.jsx` was explicitly not supposed to be changed during Step 15.

### Important Step 15 limitation

At the end of Step 15, the Search and Upload buttons were only frontend demonstrations. They were **not yet connected to FastAPI**.

## 5. Current Development Position

The project is currently at the beginning of **Step 16**.

### Step 16 goal

Connect the React PDF-upload interface to the FastAPI backend.

The intended flow is:

```text
React Frontend
      ↓
PDF Upload
      ↓
FastAPI Backend
      ↓
Validate PDF
      ↓
Save temporarily
      ↓
Return file information
      ↓
Display result on frontend
```

## 6. Backend Structure Previously Planned

The conversation proposed this structure:

```text
ResearchS
├── frontend
│   └── React + JavaScript
│
└── backend
    ├── FastAPI
    ├── PDF processing
    ├── Transformer models
    ├── Model comparison
    └── Question answering
```

A more detailed planned backend structure was:

```text
backend
├── app
│   ├── main.py
│   │
│   ├── services
│   │   ├── pdf_service.py
│   │   ├── summarization_service.py
│   │   └── qa_service.py
│   │
│   ├── models
│   │   ├── flan_t5.py
│   │   ├── bart.py
│   │   ├── long_t5.py
│   │   └── mistral.py
│   │
│   └── evaluation
│       └── model_evaluator.py
│
└── uploads
```

Treat this as the **planned architecture**. Before creating or restructuring files, inspect the actual repository because the current ZIP may differ from this planned structure.

## 7. Step-by-Step Roadmap From the Previous Development Conversation

The previous conversation established this sequence:

```text
STEP 16 → Upload PDF to backend

STEP 17 → Extract text from PDF

STEP 18 → Clean and split research paper text

STEP 19 → Test FLAN-T5 in VS Code

STEP 20 → Add BART

STEP 21 → Add LongT5

STEP 22 → Add Mistral 7B

STEP 23 → Build model comparison

STEP 24 → Evaluate outputs

STEP 25 → Select the optimal model

STEP 26 → Build PDF-based chatbot

STEP 27 → Integrate arXiv search

STEP 28 → Complete frontend integration
```

The models were intended to be tested individually from the VS Code terminal before being connected to the website.

## 8. Step 16 Backend Work Already Specified

The previous conversation instructed the developer to:

1. Open a new backend terminal.
2. Enter the `backend` directory.
3. Activate the Python virtual environment:
   `.env\Scripts\Activate.ps1`
4. Install PDF-upload support:
   `python -m pip install python-multipart`
5. Create an `uploads` directory.
6. Update `backend/app/main.py`.
7. Run the FastAPI application with:
   `python -m uvicorn app.main:app --reload`
8. Verify that the FastAPI docs expose:
   - `GET /`
   - `GET /health`
   - `POST /upload-pdf`

The proposed Step 16 API behavior was:
- Accept an uploaded file.
- Ensure the uploaded file is a PDF.
- Reject non-PDF files.
- Save the PDF temporarily in `uploads`.
- Return basic file information.

The previous conversation's proposed FastAPI configuration used:
- FastAPI
- `UploadFile`
- `File`
- `HTTPException`
- CORS middleware
- `http://localhost:5173` as the frontend origin
- `uploads` as the upload directory

## 9. Important Development Decisions

### Pretrained models, not training from scratch

Do not interpret "model training" as a requirement to train FLAN-T5, BART, LongT5, or Mistral 7B from scratch.

The established approach is:

```text
Pretrained Transformer Model
        ↓
Load model in Python
        ↓
Give research paper text
        ↓
Generate summary / answer
        ↓
Evaluate output
        ↓
Compare all 4 models
        ↓
Select best model
```

### VS Code

The previous conversation explicitly established that VS Code can be used for:
- Model development
- Testing
- Inference
- Backend development
- Running the models individually

### Hardware consideration

Mistral 7B was identified as potentially heavy for a normal laptop. Do not blindly install or run all four models simultaneously. Introduce them progressively and test individually.

## 10. Current Known State & Completed Milestones

All core roadmap milestones up to **Step 26** are fully implemented, verified, and operational:

- **Step 16 (PDF Ingestion)**: React drag-and-drop / file selector with FastAPI validation and UUID sanitization.
- **Step 17 (Text Extraction)**: High-speed PyMuPDF extraction with PyPDF fallback.
- **Step 18 (Preprocessing & Chunking)**: Hyphen rejoin, citation bracket stripping, and sentence-aware sliding window chunking.
- **Step 19 (Google FLAN-T5)**: 250M parameter instruction seq2seq model inference.
- **Step 20 (Meta BART)**: 406M parameter denoising autoencoder abstractive summarization.
- **Step 21 (Model Comparison & ROUGE)**: Side-by-side benchmarking for ROUGE-1, ROUGE-2, and ROUGE-L F1 scores with latency.
- **Step 22 (Artifact Serialization)**: Automated winning model determination and `best_model.pkl` export (Criterion 14).
- **Step 23 (arXiv Search & Import)**: Live arXiv search API integration with 1-click import into the analysis pipeline.
- **Step 24 (Single Model Summarizer)**: Interactive tab allowing dedicated summarization with model choice.
- **Step 25 (Google LongT5)**: 250M parameter Transient Global (TGlobal) attention supporting 4,096-token context windows.
- **Step 26 (PDF Q&A Chatbot)**: Offline context-grounded RAG with TF-IDF chunk retrieval, FLAN-T5 generation, and cited chunk evidence.
- **Memory Safety**: Thread-safe sequential execution with explicit VRAM purging (`torch.cuda.empty_cache()`), verified on 4GB VRAM.

## 11. Next Roadmap Steps (Future Enhancements)

1. 4-bit / 8-bit model quantization via `bitsandbytes` to evaluate 7B-parameter models (Mistral 7B) on consumer GPUs.
2. Parameter-efficient fine-tuning (PEFT / LoRA) on custom arXiv paper datasets.
3. Multi-paper cross-document synthesis.

## 12. Project Context Rule

This document summarizes the previous ChatGPT development conversation. It is project history and context, not permission to blindly modify the repository.

The actual code in the repository is the source of truth for what currently exists.

When the conversation and the code disagree:
- Inspect the code.
- Preserve working functionality.
- Do not overwrite working implementation merely to match the historical conversation.
- Explain important discrepancies before making large architectural changes.

## 13. Safety and Quality Expectations

- Do not expose API keys, passwords, tokens, or secrets.
- Do not hard-code secrets.
- Do not delete working functionality without a clear reason.
- Avoid unnecessary dependencies.
- Reuse existing components and utilities where appropriate.
- Keep frontend and backend responsibilities separated.
- Test changes incrementally.
- Do not claim a feature is complete until it has actually been tested.
