# ResearchS ✦ Frontend Web Application

[![Live App](https://img.shields.io/badge/Live%20Frontend-Render%20Cloud-46E3B7?style=flat-square&logo=render&logoColor=white)](https://researchs-frontend.onrender.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite%208-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)

The frontend client for **ResearchS**, an AI-powered academic paper assistant. Built with React 19 and Vite, providing a fast, responsive, and intuitive interface for researchers to discover papers, generate abstractive summaries, compare transformer models, and interact via an academic RAG chatbot.

---

## 🌐 Live Web Demo

* **Production URL**: [https://researchs-frontend.onrender.com](https://researchs-frontend.onrender.com)
* **Backend API**: [https://researchs-backend.onrender.com](https://researchs-backend.onrender.com)

---

## 🌟 Key Features

* **Real-time arXiv Search**: Query arXiv papers with live abstract previews and one-click import into the analysis pipeline.
* **Paper Ingestion**: Drag-and-drop PDF upload or instant loading of the pre-processed benchmark paper.
* **Pre-processing Inspection**: View extracted text metrics, de-hyphenated word counts, chunk boundaries, and citation cleanup in real time.
* **Dual Inference Modes**:
  * **Single Model Summary**: Switch between Google FLAN-T5, Meta BART, and Google LongT5 with custom summary length sliders.
  * **3-Model Comparison**: Side-by-side comparative benchmarking displaying ROUGE-1, ROUGE-2, and ROUGE-L scores with latency metrics.
* **Interactive PDF Chatbot (RAG)**: Ask contextual questions about any uploaded paper. Answers are retrieved via TF-IDF chunk ranking and displayed with citation confidence badges.

---

## 🛠️ Technology Stack

* **Framework**: React 19
* **Build Tool**: Vite 8
* **Styling**: Modern Vanilla CSS with CSS custom properties (design tokens, smooth gradients, responsive layout)
* **Icons**: Inline SVG icons optimized for performance

---

## ⚙️ Environment Configuration

The application communicates with the backend via the `VITE_API_URL` environment variable.

| Variable | Default (Local) | Production (Render) |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:8000` | `https://researchs-backend.onrender.com` |

To override locally, create a `.env` file in this directory:

```env
VITE_API_URL=http://localhost:8000
```

---

## 🚀 Getting Started

### Install Dependencies

```bash
npm install
```

### Run Local Development Server

```bash
npm run dev
```

Opens at `http://localhost:5173`.

### Production Build

```bash
npm run build
```

Builds the optimized production bundle to the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

---

## 📄 License

This project is licensed under the [MIT License](../LICENSE).
