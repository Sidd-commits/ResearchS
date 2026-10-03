import { useRef, useState } from "react";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const fileInputRef = useRef(null);

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadedPaper, setUploadedPaper] = useState(null);
  const [uploadError, setUploadError] = useState("");

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      alert("Please enter a research topic or paper title.");
      return;
    }

    alert(`arXiv search for: ${searchQuery}`);
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
    } catch (err) {
      setUploadError(err.message || "Failed to connect to backend server. Make sure the backend is running.");
    } finally {
      setUploadLoading(false);
      event.target.value = "";
    }
  };

  return (
    <div className="app">
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo">
          <div className="logo-icon">R</div>
          <span>ResearchS</span>
        </div>

        <div className="nav-links">
          <a href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </div>

        <button className="status-button">
          <span className="status-dot"></span>
          System Online
        </button>
      </nav>

      {/* Main Section */}
      <main id="home">
        <section className="hero">
          <div className="hero-badge">
            <span>✦</span>
            AI-Powered Research Assistant
          </div>

          <h1>
            Understand Research Papers
            <span> Faster with AI.</span>
          </h1>

          <p className="hero-description">
            Search research papers, upload PDFs, generate intelligent
            summaries, compare transformer models, and ask questions about
            your research.
          </p>

          {/* Search Box */}
          <div className="search-container">
            <div className="search-box">
              <span className="search-icon">⌕</span>

              <input
                type="text"
                placeholder="Search research papers on arXiv..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSearch();
                  }
                }}
              />

              <button onClick={handleSearch}>Search</button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="hero-actions">
            <button className="primary-button" onClick={handleSearch}>
              Search Papers
              <span>→</span>
            </button>

            <button
              className="secondary-button"
              onClick={handleUploadClick}
              disabled={uploadLoading}
            >
              <span>↑</span>
              {uploadLoading ? "Uploading..." : "Upload Research Paper"}
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
              Uploading and validating PDF with FastAPI backend...
            </div>
          )}

          {uploadError && (
            <div className="upload-error-banner">
              <span>⚠</span>
              <span>{uploadError}</span>
              <button onClick={() => setUploadError("")}>✕</button>
            </div>
          )}

          {uploadedPaper && (
            <div className="uploaded-card">
              <div className="uploaded-card-icon">📄</div>
              <div className="uploaded-card-info">
                <h4>{uploadedPaper.filename}</h4>
                <p>
                  Size: <strong>{uploadedPaper.file_size_kb} KB</strong> • Status:{" "}
                  <span className="success-tag">✓ Ready for Preprocessing</span>
                </p>
              </div>
              <button
                className="clear-paper-button"
                onClick={() => setUploadedPaper(null)}
                title="Remove paper"
              >
                ✕
              </button>
            </div>
          )}

          <p className="supported-text">
            Supports research papers from <strong>arXiv</strong> and PDF
            uploads
          </p>
        </section>

        {/* Features */}
        <section className="features" id="features">
          <div className="section-heading">
            <p>POWERED BY TRANSFORMERS</p>
            <h2>Everything you need to understand research.</h2>
          </div>

          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon purple">⌕</div>
              <h3>Search Papers</h3>
              <p>
                Discover research papers directly from arXiv using topics,
                keywords, or paper titles.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon blue">▤</div>
              <h3>Smart Summaries</h3>
              <p>
                Generate concise and meaningful summaries using multiple
                transformer models.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon green">✦</div>
              <h3>Model Comparison</h3>
              <p>
                Compare FLAN-T5, BART, LongT5, and Mistral to identify the
                most suitable model.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon orange">◌</div>
              <h3>Research Chatbot</h3>
              <p>
                Ask questions about your uploaded research paper and receive
                context-aware answers.
              </p>
            </div>
          </div>
        </section>

        {/* Workflow */}
        <section className="workflow" id="about">
          <div className="section-heading">
            <p>HOW IT WORKS</p>
            <h2>From research paper to understanding in minutes.</h2>
          </div>

          <div className="workflow-grid">
            <div className="workflow-step">
              <span>01</span>
              <h3>Upload or Search</h3>
              <p>Find a paper on arXiv or upload your own PDF.</p>
            </div>

            <div className="workflow-step">
              <span>02</span>
              <h3>Analyze</h3>
              <p>ResearchS extracts and processes the paper content.</p>
            </div>

            <div className="workflow-step">
              <span>03</span>
              <h3>Compare Models</h3>
              <p>Four transformer models generate and evaluate results.</p>
            </div>

            <div className="workflow-step">
              <span>04</span>
              <h3>Ask Questions</h3>
              <p>Interact with your research paper through the AI chatbot.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;