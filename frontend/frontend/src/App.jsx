import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [process, setProcess] = useState("");
  const [result, setResult] = useState(null);

  const [file, setFile] = useState(null);
  const [document, setDocument] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [ragStatus, setRagStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    checkRagStatus();
  }, []);

  const checkRagStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/rag-status");
      const data = await response.json();
      setRagStatus(data);
    } catch {
      setRagStatus({ status: "offline", documents_chunks: 0 });
    }
  };

  const uploadDocument = async () => {
    if (!file) {
      setError("Please select a PDF or DOCX file first.");
      return;
    }

    setUploading(true);
    setError("");
    setDocument(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "http://127.0.0.1:8000/upload-document",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setDocument(data);

      if (data.text_preview) {
        setProcess(data.text_preview);
      }

      await checkRagStatus();
    } catch (err) {
      setError(
        err.message ||
          "Could not upload the document. Make sure the FastAPI backend is running."
      );
    } finally {
      setUploading(false);
    }
  };

  const analyseProcess = async () => {
    if (!process.trim()) {
      setError(
        "Please describe a business process or upload a document first."
      );
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analyse",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            process: process,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Analysis failed");
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setResult(data);

      setTimeout(() => {
        document
          .getElementById("analysis-results")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(
        err.message ||
          "Could not analyse the process. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const renderList = (items) => (
    <ul>
      {items?.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  );

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI Future Process Designer</h1>
          <p>
            Transform business processes into smarter human-AI workflows.
          </p>
        </div>

        <div className="status">
          <span></span>
          AI Engine Ready
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <span className="eyebrow">ENTERPRISE AI</span>

          <h2>Design the future of your process</h2>

          <p>
            Describe your current business process or upload a process
            document. AI identifies bottlenecks, automation opportunities,
            human responsibilities and potential future workflows.
          </p>

          <div className="rag-badge">
            <span className="rag-dot"></span>
            RAG Knowledge Base:{" "}
            {ragStatus?.status === "ready"
              ? `${ragStatus.documents_chunks} chunks indexed`
              : "Checking..."}
          </div>
        </section>

        <section className="input-card">
          <label>Current Business Process</label>

          <textarea
            value={process}
            onChange={(e) => setProcess(e.target.value)}
            placeholder="Example: Employees submit leave requests by email. Managers review them. HR manually updates Excel and sends the information to payroll."
          />

          <div className="divider">
            <span>OR</span>
          </div>

          <div className="upload-section">
            <label>Upload a process document</label>

            <p className="upload-help">
              Upload a PDF or DOCX containing your business process.
            </p>

            <div className="upload-row">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => {
                  setFile(e.target.files[0]);
                  setError("");
                  setDocument(null);
                }}
              />

              <button
                className="upload-button"
                onClick={uploadDocument}
                disabled={uploading}
              >
                {uploading ? "Processing..." : "Upload Document"}
              </button>
            </div>

            {document && (
              <div className="document-success">
                <div className="success-icon">✓</div>

                <div>
                  <strong>{document.filename}</strong>

                  <p>
                    Document processed and added to the RAG knowledge base.
                    <br />
                    {document.characters_extracted} characters extracted.
                    <br />
                    <strong>{document.chunks_added}</strong> knowledge chunks
                    indexed.
                  </p>
                </div>
              </div>
            )}
          </div>

          {error && <div className="error">{error}</div>}

          <button
            className="analyse-button"
            onClick={analyseProcess}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Analysing Process...
              </>
            ) : (
              "Analyse Process →"
            )}
          </button>
        </section>

        {result && (
          <section className="results" id="analysis-results">
            <div className="section-title">
              <span className="eyebrow">AI ANALYSIS</span>

              <h2>Future Process Recommendations</h2>

              <p>
                AI-generated analysis of the current workflow and potential
                opportunities for transformation.
              </p>
            </div>

            <div className="card highlight-card">
              <div className="card-number">01</div>

              <div>
                <h3>Current Process</h3>
                <p>{result.current_process}</p>
              </div>
            </div>

            <div className="grid">
              <div className="card">
                <div className="card-number">02</div>
                <h3>Bottlenecks</h3>
                {renderList(result.bottlenecks)}
              </div>

              <div className="card">
                <div className="card-number">03</div>
                <h3>AI Opportunities</h3>
                {renderList(result.ai_opportunities)}
              </div>

              <div className="card">
                <div className="card-number">04</div>
                <h3>Human Responsibilities</h3>
                {renderList(result.human_tasks)}
              </div>

              <div className="card">
                <div className="card-number">05</div>
                <h3>Expected Benefits</h3>
                {renderList(result.benefits)}
              </div>
            </div>

            <div className="card future">
              <div className="card-number">06</div>

              <h3>Proposed Future Process</h3>

              <p className="future-description">
                A human-centred workflow combining AI, automation and human
                decision-making.
              </p>

              <div className="workflow">
                {result.future_process?.map((step, index) => (
                  <div className="workflow-step" key={index}>
                    <div className="number">{index + 1}</div>

                    <div className="workflow-content">
                      <span className="workflow-label">
                        {index === 0
                          ? "INPUT"
                          : index === result.future_process.length - 1
                          ? "OUTCOME"
                          : "PROCESS"}
                      </span>

                      <p>{step}</p>
                    </div>

                    {index < result.future_process.length - 1 && (
                      <div className="arrow">↓</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid">
              <div className="card">
                <div className="card-number">07</div>
                <h3>Risks & Considerations</h3>
                {renderList(result.risks)}
              </div>

              <div className="card">
                <div className="card-number">08</div>
                <h3>AI Recommendations</h3>
                {renderList(result.recommendations)}
              </div>
            </div>
          </section>
        )}

        <section className="info-grid">
          <div className="info-card">
            <strong>01</strong>
            <h3>Identify</h3>
            <p>
              Discover bottlenecks, repetitive work and process risks.
            </p>
          </div>

          <div className="info-card">
            <strong>02</strong>
            <h3>Redesign</h3>
            <p>
              Find opportunities for AI, automation and smarter workflows.
            </p>
          </div>

          <div className="info-card">
            <strong>03</strong>
            <h3>Decide</h3>
            <p>
              Keep important decisions and accountability with people.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;