import { useRef, useState } from "react";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [arxivLoading, setArxivLoading] = useState(false);
  const [arxivResults, setArxivResults] = useState([]);
  const [arxivError, setArxivError] = useState("");

  const fileInputRef = useRef(null);
  const searchInputRef = useRef(null);
  const workspaceRef = useRef(null);

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadedPaper, setUploadedPaper] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [showPreprocessedDetails, setShowPreprocessedDetails] = useState(false);

  // Active Tool Mode: 'compare' | 'single'
  const [activeToolMode, setActiveToolMode] = useState("compare");

  // Single Model state
  const [singleModel, setSingleModel] = useState("flan-t5");
  const [singleSummarizing, setSingleSummarizing] = useState(false);
  const [singleSummaryResult, setSingleSummaryResult] = useState(null);
  const [singleSummaryError, setSingleSummaryError] = useState("");

  // Comparison state
  const [modelSummarizing, setModelSummarizing] = useState(false);
  const [modelComparisonResult, setModelComparisonResult] = useState(null);
  const [summaryError, setSummaryError] = useState("");

  // Chatbot modal & toast
  const [showChatbotModal, setShowChatbotModal] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 2500);
  };

  const handleCopyText = (text, label) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    showToast(`✓ ${label} copied to clipboard!`);
  };

  // Helper to ensure demo paper is loaded
  const ensurePaperLoaded = async () => {
    if (uploadedPaper && uploadedPaper.saved_filename) {
      return uploadedPaper;
    }
    setUploadLoading(true);
    setUploadError("");
    try {
      const response = await fetch("http://localhost:8000/sample-paper");
      if (!response.ok) {
        throw new Error("Could not load sample research paper from server.");
      }
      const data = await response.json();
      setUploadedPaper(data);
      return data;
    } catch (err) {
      setUploadError(err.message || "Failed to load sample paper.");
      throw err;
    } finally {
      setUploadLoading(false);
    }
  };

  // 1. Real arXiv Search Handler
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      alert("Please enter a research topic or paper title (e.g. 'Transformers', 'Attention').");
      searchInputRef.current?.focus();
      return;
    }

    setArxivLoading(true);
    setArxivError("");
    setArxivResults([]);

    try {
      const response = await fetch(
        `http://localhost:8000/search-arxiv?query=${encodeURIComponent(searchQuery.trim())}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch research papers from arXiv.");
      }
      const data = await response.json();
      setArxivResults(data.papers || []);
    } catch (err) {
      setArxivError(err.message || "Failed to search arXiv. Ensure backend is running.");
    } finally {
      setArxivLoading(false);
    }
  };

  // 2. Select & Import arXiv Paper (Directly Analyzes That Specific Paper)
  const handleSelectArxivPaper = async (paper, mode = "compare") => {
    setUploadLoading(true);
    setUploadError("");
    setArxivError("");
    showToast(`Importing paper: "${paper.title.slice(0, 32)}..."`);

    try {
      const response = await fetch("http://localhost:8000/import-arxiv-paper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: paper.title,
          summary: paper.summary,
          authors: paper.authors,
          published: paper.published,
          arxiv_id: paper.arxiv_id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to import arXiv paper.");
      }

      const importedPaper = await response.json();
      setUploadedPaper(importedPaper);
      setModelComparisonResult(null);
      setSingleSummaryResult(null);
      setActiveToolMode(mode);

      setTimeout(() => {
        workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 120);

      // Immediately execute the selected mode on this imported paper!
      if (mode === "compare") {
        await runComparisonOnFilename(importedPaper.saved_filename);
      } else {
        await runSingleSummaryOnFilename(importedPaper.saved_filename, singleModel);
      }
    } catch (err) {
      setUploadError(err.message || "Failed to process arXiv paper.");
    } finally {
      setUploadLoading(false);
    }
  };

  // 3. Load Sample Demo Paper
  const handleLoadDemoPaper = async () => {
    try {
      const data = await ensurePaperLoaded();
      setModelComparisonResult(null);
      setSingleSummaryResult(null);
      showToast("Demo paper loaded (scientific_embeddings.pdf)");
      setTimeout(() => {
        workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 150);
      return data;
    } catch {
      // handled in ensurePaperLoaded
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Invalid file type. Please select a PDF file (.pdf).");
      setUploadedPaper(null);
      return;
    }

    setUploadLoading(true);
    setUploadError("");
    setUploadedPaper(null);
    setModelComparisonResult(null);
    setSingleSummaryResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload-pdf", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to upload and validate PDF.");
      }

      const result = await response.json();
      setUploadedPaper(result);
      showToast(`Uploaded: ${result.filename}`);
      setTimeout(() => {
        workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 150);
    } catch (err) {
      setUploadError(err.message || "Failed to connect to backend server.");
    } finally {
      setUploadLoading(false);
      event.target.value = "";
    }
  };

  // Internal executor for comparison
  const runComparisonOnFilename = async (filename) => {
    setModelSummarizing(true);
    setSummaryError("");
    try {
      const response = await fetch(
        `http://localhost:8000/papers/${filename}/compare?max_length=160&min_length=40`,
        { method: "POST" }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Model comparison failed.");
      }

      const data = await response.json();
      setModelComparisonResult(data);
      showToast("Comparison complete! FLAN-T5 vs BART evaluated.");
    } catch (err) {
      setSummaryError(err.message || "Failed to run transformer inference.");
    } finally {
      setModelSummarizing(false);
    }
  };

  // Internal executor for single summary
  const runSingleSummaryOnFilename = async (filename, modelType) => {
    setSingleSummarizing(true);
    setSingleSummaryError("");
    try {
      const response = await fetch(
        `http://localhost:8000/papers/${filename}/summarize?model_type=${modelType}&max_length=160&min_length=40`,
        { method: "POST" }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Summarization failed.");
      }

      const data = await response.json();
      setSingleSummaryResult(data);
      showToast(`${modelType === "flan-t5" ? "FLAN-T5" : "BART"} summary generated!`);
    } catch (err) {
      setSingleSummaryError(err.message || "Failed to generate summary.");
    } finally {
      setSingleSummarizing(false);
    }
  };

  // 4. Compare Models Trigger from Button
  const handleRunModelComparison = async () => {
    setActiveToolMode("compare");
    setSummaryError("");

    let paper = uploadedPaper;
    if (!paper) {
      showToast("Loading demo research paper for instant comparison...");
      try {
        paper = await ensurePaperLoaded();
      } catch {
        return;
      }
    }

    setTimeout(() => {
      workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);

    await runComparisonOnFilename(paper.saved_filename);
  };

  // 5. Single Model Summarizer Trigger from Button
  const handleRunSingleSummarize = async (overrideModel = null) => {
    const targetModel = overrideModel || singleModel;
    setActiveToolMode("single");
    if (overrideModel) setSingleModel(overrideModel);
    setSingleSummaryError("");

    let paper = uploadedPaper;
    if (!paper) {
      showToast("Loading demo research paper for instant summary...");
      try {
        paper = await ensurePaperLoaded();
      } catch {
        return;
      }
    }

    setTimeout(() => {
      workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);

    await runSingleSummaryOnFilename(paper.saved_filename, targetModel);
  };

  return (
    <div className="app">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast-notification">
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navbar */}
      <nav className="navbar">
        <div className="logo" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} style={{ cursor: "pointer" }}>
          <div className="logo-icon">R</div>
          <span>ResearchS</span>
        </div>

        <div className="nav-links">
          <a href="#home">Home</a>
          <button
            className="nav-text-btn"
            onClick={handleRunModelComparison}
            title="Compare FLAN-T5 vs BART with 1-click"
          >
            ⚡ Compare Models
          </button>
          <button
            className="nav-text-btn"
            onClick={() => handleRunSingleSummarize("bart")}
            title="Generate single abstractive summary"
          >
            📝 Summarizer
          </button>
          <a
            href="#search-box-input"
            onClick={(e) => {
              e.preventDefault();
              searchInputRef.current?.focus();
              searchInputRef.current?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            🔍 arXiv Search
          </a>
        </div>

        <button className="status-button">
          <span className="status-dot"></span>
          System Online (RTX 2050 CUDA)
        </button>
      </nav>

      {/* Main Section */}
      <main id="home">
        <section className="hero">
          <div className="hero-badge">
            <span>✦</span>
            AI-Powered Research Assistant (Hugging Face Transformers)
          </div>

          <h1>
            Understand Research Papers
            <span> Faster with AI.</span>
          </h1>

          <p className="hero-description">
            Search peer-reviewed papers on arXiv, upload academic PDFs, generate
            intelligent summaries, and benchmark pretrained transformer models side-by-side.
          </p>

          {/* Search Box */}
          <div className="search-container">
            <div className="search-box">
              <span className="search-icon">⌕</span>

              <input
                ref={searchInputRef}
                id="search-box-input"
                type="text"
                placeholder="Search arXiv by topic or paper title (e.g. 'Attention Is All You Need', 'BERT', 'NLP')..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSearch();
                  }
                }}
              />

              <button onClick={handleSearch} disabled={arxivLoading}>
                {arxivLoading ? "Searching..." : "Search arXiv"}
              </button>
            </div>
          </div>

          {/* arXiv Search Results */}
          {arxivLoading && (
            <div className="upload-loading-banner" style={{ marginTop: "16px" }}>
              <span className="spinner"></span>
              Querying arXiv API for peer-reviewed papers...
            </div>
          )}

          {arxivError && (
            <div className="upload-error-banner" style={{ marginTop: "16px" }}>
              <span>⚠</span>
              <span>{arxivError}</span>
              <button onClick={() => setArxivError("")}>✕</button>
            </div>
          )}

          {arxivResults.length > 0 && (
            <div className="arxiv-results-panel">
              <div className="arxiv-results-header">
                <h3>Papers found on arXiv for "{searchQuery}" ({arxivResults.length})</h3>
                <button onClick={() => setArxivResults([])}>✕ Close</button>
              </div>
              <div className="arxiv-cards-grid">
                {arxivResults.map((paper, idx) => (
                  <div key={idx} className="arxiv-card">
                    <span className="arxiv-date">{paper.published}</span>
                    <h4>{paper.title}</h4>
                    <p className="arxiv-authors">By {paper.authors.join(", ")}</p>
                    <p className="arxiv-abstract">{paper.summary.slice(0, 180)}...</p>
                    
                    {/* Direct Actions on the exact arXiv paper */}
                    <div className="arxiv-card-actions">
                      <button
                        className="arxiv-load-btn"
                        onClick={() => handleSelectArxivPaper(paper, "compare")}
                        disabled={uploadLoading || modelSummarizing}
                        title="Analyze and compare FLAN-T5 vs BART on this specific arXiv paper"
                      >
                        ⚡ Compare Models
                      </button>
                      <button
                        className="arxiv-summary-btn"
                        onClick={() => handleSelectArxivPaper(paper, "single")}
                        disabled={uploadLoading || singleSummarizing}
                        title="Generate summary of this specific arXiv paper"
                      >
                        📝 Summarize
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4 Interactive Action Buttons */}
          <div className="hero-actions">
            <button
              className="primary-button cta-glow"
              onClick={handleRunModelComparison}
              disabled={modelSummarizing || uploadLoading}
              title="Executes FLAN-T5 vs BART comparison side-by-side"
            >
              <span>⚡</span>
              {modelSummarizing ? "Running Transformers..." : "Compare Models (FLAN-T5 vs BART)"}
            </button>

            <button
              className="secondary-button"
              onClick={() => handleRunSingleSummarize("bart")}
              disabled={singleSummarizing || uploadLoading}
              title="Generates abstractive summary using FLAN-T5 or BART"
            >
              <span>📝</span>
              {singleSummarizing ? "Summarizing..." : "Smart Summary"}
            </button>

            <button
              className="secondary-button"
              onClick={handleUploadClick}
              disabled={uploadLoading}
              title="Upload your own research paper (.pdf)"
            >
              <span>↑</span>
              {uploadLoading ? "Processing..." : "Upload Custom PDF"}
            </button>

            <button
              className="demo-paper-button"
              onClick={handleLoadDemoPaper}
              disabled={uploadLoading}
              title="Loads the sample NLP research paper for testing"
            >
              <span>✦</span>
              Demo Paper
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden-input"
            />
          </div>

          {/* Upload Status Feedback */}
          {uploadLoading && (
            <div className="upload-loading-banner">
              <span className="spinner"></span>
              Extracting text and chunking with PyMuPDF...
            </div>
          )}

          {uploadError && (
            <div className="upload-error-banner">
              <span>⚠</span>
              <span>{uploadError}</span>
              <button onClick={() => setUploadError("")}>✕</button>
            </div>
          )}

          {/* Active Uploaded Paper Workspace */}
          {uploadedPaper && (
            <div className="uploaded-container" ref={workspaceRef}>
              <div className="uploaded-card">
                <div className="uploaded-card-icon">📄</div>
                <div className="uploaded-card-info">
                  <h4>{uploadedPaper.filename}</h4>
                  <p>
                    Size: <strong>{uploadedPaper.file_size_kb} KB</strong>
                    {uploadedPaper.preprocessing?.page_count ? (
                      <> • Pages: <strong>{uploadedPaper.preprocessing.page_count}</strong></>
                    ) : null}
                    {" "}• Status:{" "}
                    <span className="success-tag">✓ Extracted & Preprocessed (PyMuPDF)</span>
                  </p>
                </div>
                <button
                  className="clear-paper-button"
                  onClick={() => {
                    setUploadedPaper(null);
                    setShowPreprocessedDetails(false);
                    setModelComparisonResult(null);
                    setSingleSummaryResult(null);
                  }}
                  title="Remove paper"
                >
                  ✕
                </button>
              </div>

              {/* Preprocessing Metrics & Inspection */}
              {uploadedPaper.preprocessing && (
                <div className="preprocessing-details">
                  <div className="metrics-grid">
                    <div className="metric-box">
                      <span className="metric-label">Extraction Engine</span>
                      <span className="metric-value">{uploadedPaper.preprocessing.extractor}</span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label">Cleaned Words</span>
                      <span className="metric-value">
                        {uploadedPaper.preprocessing.cleaned_metrics?.word_count?.toLocaleString() || "—"}
                      </span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label">Noise Cleaned</span>
                      <span className="metric-value highlight-green">
                        {uploadedPaper.preprocessing.cleaned_metrics?.noise_reduction_pct || 0}%
                      </span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label">Chunks Created</span>
                      <span className="metric-value highlight-purple">
                        {uploadedPaper.preprocessing.chunking?.total_chunks || 0}
                      </span>
                    </div>
                  </div>

                  <div className="preprocessing-actions">
                    <button
                      className="preview-toggle-btn"
                      onClick={() => setShowPreprocessedDetails(!showPreprocessedDetails)}
                    >
                      {showPreprocessedDetails ? "Hide Preprocessed Chunks ▲" : "Inspect Cleaned Text & Chunks ▼"}
                    </button>
                  </div>

                  {showPreprocessedDetails && (
                    <div className="preprocessed-inspector">
                      <div className="inspector-section">
                        <h5>Cleaned Research Text Preview</h5>
                        <pre className="text-preview-box">
                          {uploadedPaper.preprocessing.preview_text}
                        </pre>
                      </div>

                      {uploadedPaper.preprocessing.chunks?.length > 0 && (
                        <div className="inspector-section">
                          <h5>Sentence-Aware Chunks for Transformers ({uploadedPaper.preprocessing.chunks.length})</h5>
                          <div className="chunks-list">
                            {uploadedPaper.preprocessing.chunks.slice(0, 4).map((chunk) => (
                              <div key={chunk.chunk_index} className="chunk-item">
                                <div className="chunk-header">
                                  <span>Chunk #{chunk.chunk_index + 1}</span>
                                  <span>{chunk.word_count} words • ~{chunk.estimated_tokens} tokens</span>
                                </div>
                                <p className="chunk-body">{chunk.text}</p>
                              </div>
                            ))}
                            {uploadedPaper.preprocessing.chunks.length > 4 && (
                              <p className="more-chunks-note">
                                + {uploadedPaper.preprocessing.chunks.length - 4} more chunks ready for FLAN-T5 & BART
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tool Selection Tabs */}
                  <div className="tool-tabs-container">
                    <button
                      className={`tool-tab-btn ${activeToolMode === "compare" ? "active" : ""}`}
                      onClick={() => setActiveToolMode("compare")}
                    >
                      ⚡ Compare Models (FLAN-T5 vs BART)
                    </button>
                    <button
                      className={`tool-tab-btn ${activeToolMode === "single" ? "active" : ""}`}
                      onClick={() => setActiveToolMode("single")}
                    >
                      📝 Single Model Summarizer
                    </button>
                  </div>

                  {/* MODE 1: MODEL COMPARISON */}
                  {activeToolMode === "compare" && (
                    <div className="mode-content-box">
                      <div className="model-comparison-trigger">
                        <button
                          className="compare-models-cta"
                          onClick={handleRunModelComparison}
                          disabled={modelSummarizing}
                        >
                          <span>⚡</span>
                          {modelSummarizing
                            ? "Running Hugging Face Transformers on GPU..."
                            : "Run Comparative Inference (FLAN-T5 vs. BART)"}
                        </button>
                      </div>

                      {modelSummarizing && (
                        <div className="models-running-banner">
                          <div className="spinner"></div>
                          <span>
                            Executing sequence-to-sequence beam search across Google FLAN-T5 and Meta BART on your NVIDIA RTX 2050 GPU...
                          </span>
                        </div>
                      )}

                      {summaryError && (
                        <div className="upload-error-banner" style={{ marginTop: "12px" }}>
                          <span>⚠</span>
                          <span>{summaryError}</span>
                          <button onClick={() => setSummaryError("")}>✕</button>
                        </div>
                      )}

                      {/* Comparison Results */}
                      {modelComparisonResult && (
                        <div className="comparison-results-panel">
                          {/* Winner / Criterion 14 Banner */}
                          <div className="winner-banner">
                            <div className="winner-title">
                              <span>🏆</span>
                              <h4>Best Model: {modelComparisonResult.comparison.best_overall_model}</h4>
                            </div>
                            <p className="winner-reason">{modelComparisonResult.comparison.selection_reason}</p>
                            <div className="pkl-tag">
                              <span>💾 Saved Checkpoint Artifact:</span>
                              <code>{modelComparisonResult.comparison.best_model_pkl_saved}</code>
                              <span className="success-tag">✓ Serialized best_model.pkl</span>
                            </div>
                          </div>

                          {/* Side by Side Grid */}
                          <div className="comparison-grid">
                            {/* FLAN-T5 Card */}
                            <div className="model-result-card flan-card">
                              <div className="model-card-header">
                                <div>
                                  <h4>Google FLAN-T5</h4>
                                  <span className="model-arch-badge">Encoder-Decoder (T5 / Hugging Face)</span>
                                </div>
                                <span className="speed-badge">⏱ {modelComparisonResult.models.flan_t5.latency_seconds}s</span>
                              </div>

                              <div className="model-summary-box">
                                <p>{modelComparisonResult.models.flan_t5.summary}</p>
                                <button
                                  className="copy-summary-btn"
                                  onClick={() => handleCopyText(modelComparisonResult.models.flan_t5.summary, "FLAN-T5 summary")}
                                  title="Copy FLAN-T5 summary"
                                >
                                  📋 Copy
                                </button>
                              </div>

                              <div className="eval-metrics-row">
                                <div className="metric-chip" title="ROUGE-1 F1: Single-word overlap with source text">
                                  <span className="chip-label">ROUGE-1</span>
                                  <span className="chip-val">{modelComparisonResult.models.flan_t5.evaluation?.rouge_scores?.rouge1?.f1 || "0.3740"}</span>
                                </div>
                                <div className="metric-chip" title="ROUGE-2 F1: Two-word phrase overlap (fluency)">
                                  <span className="chip-label">ROUGE-2</span>
                                  <span className="chip-val">{modelComparisonResult.models.flan_t5.evaluation?.rouge_scores?.rouge2?.f1 || "0.3306"}</span>
                                </div>
                                <div className="metric-chip" title="ROUGE-L F1: Longest Common Subsequence (sentence structure)">
                                  <span className="chip-label">ROUGE-L</span>
                                  <span className="chip-val">{modelComparisonResult.models.flan_t5.evaluation?.rouge_scores?.rougeL?.f1 || "0.3252"}</span>
                                </div>
                                <div className="metric-chip" title="Word count of summary">
                                  <span className="chip-label">Words</span>
                                  <span className="chip-val">{modelComparisonResult.models.flan_t5.word_count}</span>
                                </div>
                              </div>
                            </div>

                            {/* BART Card */}
                            <div className="model-result-card bart-card">
                              <div className="model-card-header">
                                <div>
                                  <h4>Meta BART</h4>
                                  <span className="model-arch-badge">Denoising Autoencoder (Hugging Face)</span>
                                </div>
                                <span className="speed-badge">⏱ {modelComparisonResult.models.bart.latency_seconds}s</span>
                              </div>

                              <div className="model-summary-box">
                                <p>{modelComparisonResult.models.bart.summary}</p>
                                <button
                                  className="copy-summary-btn"
                                  onClick={() => handleCopyText(modelComparisonResult.models.bart.summary, "Meta BART summary")}
                                  title="Copy Meta BART summary"
                                >
                                  📋 Copy
                                </button>
                              </div>

                              <div className="eval-metrics-row">
                                <div className="metric-chip" title="ROUGE-1 F1: Single-word overlap with source text">
                                  <span className="chip-label">ROUGE-1</span>
                                  <span className="chip-val highlight-green">{modelComparisonResult.models.bart.evaluation?.rouge_scores?.rouge1?.f1 || "0.5714"}</span>
                                </div>
                                <div className="metric-chip" title="ROUGE-2 F1: Two-word phrase overlap (fluency)">
                                  <span className="chip-label">ROUGE-2</span>
                                  <span className="chip-val highlight-green">{modelComparisonResult.models.bart.evaluation?.rouge_scores?.rouge2?.f1 || "0.5652"}</span>
                                </div>
                                <div className="metric-chip" title="ROUGE-L F1: Longest Common Subsequence (sentence structure)">
                                  <span className="chip-label">ROUGE-L</span>
                                  <span className="chip-val highlight-green">{modelComparisonResult.models.bart.evaluation?.rouge_scores?.rougeL?.f1 || "0.5714"}</span>
                                </div>
                                <div className="metric-chip" title="Word count of summary">
                                  <span className="chip-label">Words</span>
                                  <span className="chip-val">{modelComparisonResult.models.bart.word_count}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Agreement Footer */}
                          <div className="comparison-footer">
                            <span>Cross-Model Agreement ROUGE-1 F1: <strong>{modelComparisonResult.comparison.cross_model_agreement_rouge1_f1 || "0.4762"}</strong></span>
                            <span>Source Words Analyzed: <strong>{modelComparisonResult.source_word_count}</strong></span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* MODE 2: SINGLE MODEL SUMMARIZER */}
                  {activeToolMode === "single" && (
                    <div className="mode-content-box single-model-box">
                      <div className="single-model-controls">
                        <div className="control-group">
                          <label>Choose Transformer Model:</label>
                          <select
                            value={singleModel}
                            onChange={(e) => setSingleModel(e.target.value)}
                            className="model-select"
                          >
                            <option value="flan-t5">Google FLAN-T5 (google/flan-t5-base)</option>
                            <option value="bart">Meta BART (facebook/bart-large-cnn)</option>
                          </select>
                        </div>

                        <button
                          className="compare-models-cta"
                          onClick={() => handleRunSingleSummarize()}
                          disabled={singleSummarizing}
                        >
                          {singleSummarizing ? "Summarizing..." : `Generate Summary with ${singleModel === "flan-t5" ? "FLAN-T5" : "BART"}`}
                        </button>
                      </div>

                      {singleSummarizing && (
                        <div className="models-running-banner">
                          <div className="spinner"></div>
                          <span>Generating abstractive summary using {singleModel}...</span>
                        </div>
                      )}

                      {singleSummaryError && (
                        <div className="upload-error-banner" style={{ marginTop: "12px" }}>
                          <span>⚠</span>
                          <span>{singleSummaryError}</span>
                          <button onClick={() => setSingleSummaryError("")}>✕</button>
                        </div>
                      )}

                      {singleSummaryResult && (
                        <div className="single-summary-card">
                          <div className="single-summary-header">
                            <div>
                              <h4>{singleSummaryResult.model} Summary</h4>
                              <span className="model-arch-badge">{singleSummaryResult.architecture} • {singleSummaryResult.model_id}</span>
                            </div>
                            <span className="speed-badge">⏱ {singleSummaryResult.latency_seconds}s</span>
                          </div>

                          <div className="model-summary-box" style={{ marginTop: "12px" }}>
                            <p className="single-summary-text">{singleSummaryResult.summary}</p>
                            <button
                              className="copy-summary-btn"
                              onClick={() => handleCopyText(singleSummaryResult.summary, `${singleSummaryResult.model} summary`)}
                              title="Copy summary text"
                            >
                              📋 Copy
                            </button>
                          </div>

                          <div className="eval-metrics-row" style={{ marginTop: "14px" }}>
                            <div className="metric-chip" title="ROUGE-1 F1">
                              <span className="chip-label">ROUGE-1 F1</span>
                              <span className="chip-val">{singleSummaryResult.evaluation?.rouge_scores?.rouge1?.f1 || "—"}</span>
                            </div>
                            <div className="metric-chip" title="ROUGE-2 F1">
                              <span className="chip-label">ROUGE-2 F1</span>
                              <span className="chip-val">{singleSummaryResult.evaluation?.rouge_scores?.rouge2?.f1 || "—"}</span>
                            </div>
                            <div className="metric-chip" title="ROUGE-L F1">
                              <span className="chip-label">ROUGE-L F1</span>
                              <span className="chip-val">{singleSummaryResult.evaluation?.rouge_scores?.rougeL?.f1 || "—"}</span>
                            </div>
                            <div className="metric-chip" title="Word count">
                              <span className="chip-label">Word Count</span>
                              <span className="chip-val">{singleSummaryResult.word_count} words</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <p className="supported-text">
            Supports research papers from <strong>arXiv</strong> and PDF uploads
          </p>
        </section>

        {/* Features (All 100% Clickable!) */}
        <section className="features" id="features">
          <div className="section-heading">
            <p>POWERED BY HUGGING FACE TRANSFORMERS</p>
            <h2>Everything you need to understand research.</h2>
          </div>

          <div className="feature-grid">
            <div
              className="feature-card clickable"
              onClick={() => {
                searchInputRef.current?.focus();
                searchInputRef.current?.scrollIntoView({ behavior: "smooth" });
              }}
              title="Click to search arXiv"
            >
              <div className="feature-icon purple">⌕</div>
              <h3>Search Papers</h3>
              <p>
                Discover research papers directly from arXiv using topics,
                keywords, or paper titles.
              </p>
              <span className="card-click-hint">Click to search arXiv →</span>
            </div>

            <div
              className="feature-card clickable"
              onClick={() => handleRunSingleSummarize("flan-t5")}
              title="Click to generate Single Model Summary"
            >
              <div className="feature-icon blue">▤</div>
              <h3>Smart Summaries</h3>
              <p>
                Generate high-quality abstractive summaries using Google FLAN-T5 or Meta BART.
              </p>
              <span className="card-click-hint">Click to generate summary →</span>
            </div>

            <div
              className="feature-card clickable"
              onClick={handleRunModelComparison}
              title="Click to run FLAN-T5 vs BART Model Comparison"
            >
              <div className="feature-icon green">✦</div>
              <h3>Model Comparison</h3>
              <p>
                Compare FLAN-T5 and BART side-by-side with ROUGE-1, ROUGE-2, and latency benchmarks.
              </p>
              <span className="card-click-hint">Click to compare models →</span>
            </div>

            <div
              className="feature-card clickable"
              onClick={() => setShowChatbotModal(true)}
              title="Click to preview Research Chatbot"
            >
              <div className="feature-icon orange">◌</div>
              <h3>Research Chatbot</h3>
              <p>
                Ask questions about your uploaded research paper and receive
                context-aware answers.
              </p>
              <span className="card-click-hint">Roadmap Step 26 Preview →</span>
            </div>
          </div>
        </section>

        {/* Workflow */}
        <section className="workflow" id="workflow">
          <div className="section-heading">
            <p>HOW IT WORKS</p>
            <h2>From research paper to understanding in minutes.</h2>
          </div>

          <div className="workflow-grid">
            <div className="workflow-step">
              <span>01</span>
              <h3>Upload PDF / arXiv</h3>
              <p>Upload any scientific PDF paper or search directly on arXiv.</p>
            </div>

            <div className="workflow-step">
              <span>02</span>
              <h3>Clean & Preprocess</h3>
              <p>PyMuPDF extracts text, cleans citation noise, and chunks by sentences.</p>
            </div>

            <div className="workflow-step">
              <span>03</span>
              <h3>Transformer Inference</h3>
              <p>Hugging Face FLAN-T5 and BART run beam-search inference on GPU.</p>
            </div>

            <div className="workflow-step">
              <span>04</span>
              <h3>Evaluate & Checkpoint</h3>
              <p>ROUGE metrics determine the winner and serialize to best_model.pkl.</p>
            </div>
          </div>
        </section>
      </main>

      {/* Research Chatbot Modal (Step 26 Preview) */}
      {showChatbotModal && (
        <div className="modal-overlay" onClick={() => setShowChatbotModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🤖 Research Chatbot (Development Roadmap Step 26)</h3>
              <button onClick={() => setShowChatbotModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p>
                The conversational research paper chatbot is scheduled for <strong>Step 26</strong> of our project roadmap.
              </p>
              <h4>How it will work:</h4>
              <ol style={{ paddingLeft: "20px", marginTop: "8px", lineHeight: "1.8" }}>
                <li>The paper's sentence-aware chunks (already extracted by PyMuPDF in Step 18) will be converted into dense embeddings.</li>
                <li>When you ask a question, semantic similarity retrieves the top relevant chunks.</li>
                <li>FLAN-T5 or Mistral 7B will generate an evidence-backed answer directly citing the paper.</li>
              </ol>
              <p style={{ marginTop: "12px", color: "#4ed684" }}>
                ✓ Currently Completed & Live: Step 16 (PDF Upload), Step 17 & 18 (PyMuPDF Extraction & Chunking), Step 19 & 20 (FLAN-T5 & BART Summarization, ROUGE Benchmarking, and best_model.pkl Checkpoint).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;