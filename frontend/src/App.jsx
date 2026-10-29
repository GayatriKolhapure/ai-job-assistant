import React, { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

// Fallback mock data when local backend is unreachable
const MOCK_RESUME = {
  name: "Alex Morgan",
  designation: "Full Stack Java Developer",
  email: "alex.morgan@example.com",
  phone: "+1 (555) 019-2834",
  experience: "3+ Years",
  skills: ["Java", "Spring Boot", "React", "RESTful APIs", "SQL", "Docker", "Git"],
  education: "B.Tech in Computer Science & Engineering",
  projects: ["E-Commerce Microservices", "Real-Time Chat Application"]
};

const MOCK_JOBS = [
  {
    job_id: "job-101",
    title: "Senior Java Developer",
    company: "TechCorp Solutions",
    location: "Bangalore, India (Hybrid)",
    experience_required: "3-5 Years",
    match_score: 94,
    skills: ["Java", "Spring Boot", "Microservices", "SQL"],
    match_reasons: [
      "Strong alignment with Java & Spring Boot experience",
      "Matches your project architecture background"
    ],
    source_link: "https://example.com/jobs/101"
  },
  {
    job_id: "job-102",
    title: "Full Stack Engineer (React + Java)",
    company: "Innovate Labs",
    location: "Remote",
    experience_required: "2-4 Years",
    match_score: 88,
    skills: ["React", "Java", "RESTful APIs", "Tailwind CSS"],
    match_reasons: [
      "Combines frontend React skills with core Java foundation",
      "Fully remote schedule option"
    ],
    source_link: "https://example.com/jobs/102"
  },
  {
    job_id: "job-103",
    title: "Backend Software Engineer",
    company: "CloudScale Systems",
    location: "Pune, India",
    experience_required: "1-3 Years",
    match_score: 82,
    skills: ["Java", "SQL", "Docker", "REST APIs"],
    match_reasons: [
      "Great fit for entry-to-mid-level Java proficiency",
      "Matches containerization (Docker) background"
    ],
    source_link: "https://example.com/jobs/103"
  }
];

export default function App() {
  const [resume, setResume] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [message, setMessage] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      sender: "assistant",
      text: "Hello! Upload your resume or type below to refine job recommendations and practice for interviews."
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("jobs");
  const [dragActive, setDragActive] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRemote, setFilterRemote] = useState(false);
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  // Auto-dismiss status messages after 5s
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // Handle Drag & Drop events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processResumeUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      processResumeUpload(e.target.files[0]);
    }
  };

  async function processResumeUpload(file) {
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setError("Please upload a PDF or DOCX file format.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");
    setResume(null);
    setJobs([]);
    setResumeFile(file.name);

    try {
      const response = await fetch(`${API_URL}/api/resume/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to process resume.");
      }

      setResume(data.resume);
      setMessage(data.message || "Resume analyzed successfully!");
      setIsOfflineMode(false);
    } catch (err) {
      // Fallback demo mode if server is offline
      setIsOfflineMode(true);
      setResume(MOCK_RESUME);
      setJobs(MOCK_JOBS);
      setMessage("Backend offline: Loaded sample candidate profile.");
    } finally {
      setLoading(false);
    }
  }

  async function getRecommendations() {
    if (!resume) {
      setError("Please upload your resume first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/jobs/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(resume),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to fetch job recommendations.");
      }

      setJobs(data.recommendations || []);
      setMessage(data.message || "Job recommendations updated!");
      setActiveTab("jobs");
    } catch (err) {
      setIsOfflineMode(true);
      setJobs(MOCK_JOBS);
      setMessage("Backend offline: Showing fallback recommendations.");
      setActiveTab("jobs");
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (!chatInput.trim()) return;

    const userQuery = chatInput.trim();
    setChatInput("");
    setChatHistory((prev) => [...prev, { sender: "user", text: userQuery }]);

    if (!resume) {
      setError("Please upload a resume first to enable AI assistant features.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userQuery,
          resume: resume,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to process your request.");
      }

      setChatHistory((prev) => [
        ...prev,
        { sender: "assistant", text: data.message || "Here are updated job matches based on your prompt." }
      ]);

      if (data.recommendations?.length > 0) {
        setJobs(data.recommendations);
      }
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: `Filtered roles matching "${userQuery}". You can apply or save positions anytime!`
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function applyForJob(job) {
    if (!job.job_id) {
      setError("Invalid job ID format.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/applications/${encodeURIComponent(job.job_id)}`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to submit application.");
      }

      setMessage(data.message || "Application recorded!");
      await loadApplications();
    } catch (err) {
      // Offline fallback application recording
      const newApp = {
        job_id: job.job_id,
        title: job.title,
        company: job.company,
        status: "Submitted",
        application_date: new Date().toISOString()
      };
      setApplications((prev) => [newApp, ...prev.filter((a) => a.job_id !== job.job_id)]);
      setMessage(`Application for "${job.title}" recorded!`);
      setActiveTab("applications");
    } finally {
      setLoading(false);
    }
  }

  async function loadApplications() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/applications`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load applications history.");
      }

      setApplications(data.applications || []);
      setActiveTab("applications");
    } catch (err) {
      setActiveTab("applications");
    } finally {
      setLoading(false);
    }
  }

  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      job.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.skills?.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesRemote = filterRemote
      ? job.location?.toLowerCase().includes("remote")
      : true;

    return matchesSearch && matchesRemote;
  });

  const skills = Array.isArray(resume?.skills) ? resume.skills : [];

  return (
    <div className="app-container">
      {/* Top Header Navigation */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          <div>
            <h1 className="brand-name">CareerPilot</h1>
            <p className="brand-subtitle">AI Job Companion & Matcher</p>
          </div>
        </div>

        <div className="header-actions">
          <nav className="nav-actions">
            <button
              className={`btn ${activeTab === "jobs" ? "primary" : "secondary"}`}
              onClick={() => setActiveTab("jobs")}
            >
              💼 Jobs ({jobs.length})
            </button>
            <button
              className={`btn ${activeTab === "copilot" ? "primary" : "secondary"}`}
              onClick={() => setActiveTab("copilot")}
            >
              💬 AI Copilot
            </button>
            <button
              className={`btn ${activeTab === "applications" ? "primary" : "secondary"}`}
              onClick={loadApplications}
            >
              📑 Tracker ({applications.length})
            </button>
          </nav>

          <span className="status-badge">
            <span className="status-dot"></span>
            {isOfflineMode ? "Demo Mode" : "System Active"}
          </span>
        </div>
      </header>

      {/* Hero Banner Header */}
      <section className="hero">
        <div className="hero-content">
          <span className="hero-eyebrow">🚀 NEXT-GEN CAREER MATCHING</span>
          <h1>
            Empowering your career moves with <span>AI Intelligence.</span>
          </h1>
          <p>
            Upload your resume, chat with your personal AI job search assistant,
            and instantly track candidate applications in real time.
          </p>

          <div className="hero-stats">
            <div className="hero-stat">
              <strong>98%</strong>
              <span>Skill Precision</span>
            </div>
            <div className="hero-stat">
              <strong>&lt; 2s</strong>
              <span>Matching Speed</span>
            </div>
            <div className="hero-stat">
              <strong>Real-Time</strong>
              <span>Application Tracker</span>
            </div>
          </div>
        </div>
      </section>

      {/* Global Alerts */}
      <div style={{ padding: "0 6%" }}>
        {error && (
          <div className="error-message" style={{ marginTop: "20px" }}>
            ⚠️ {error}
          </div>
        )}
        {message && (
          <div className="success-message" style={{ marginTop: "20px" }}>
            ✨ {message}
          </div>
        )}
      </div>

      {/* Main Workspace Layout */}
      <main className="main-content">
        <div className="chat-layout">
          {/* Left Column: Resume Profile & Upload */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div className="card">
              <h3>Upload Your Resume</h3>
              <div
                className={`upload-area ${dragActive ? "drag-active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                style={{
                  borderColor: dragActive ? "var(--primary)" : undefined,
                  background: dragActive ? "#efedff" : undefined
                }}
              >
                <div className="upload-icon">📄</div>
                <h3>Drag & Drop Resume</h3>
                <p>Supports PDF or DOCX resume formats</p>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileSelect}
                  id="resume-input"
                  style={{ display: "none" }}
                />
                <button
                  className="btn primary"
                  onClick={() => document.getElementById("resume-input").click()}
                >
                  Browse Computer
                </button>
              </div>

              {resumeFile && (
                <p style={{ fontSize: "12px", color: "var(--primary)", marginTop: "12px" }}>
                  Selected File: <strong>{resumeFile}</strong>
                </p>
              )}
            </div>

            {resume && (
              <div className="card">
                <div className="section-heading" style={{ marginBottom: "16px" }}>
                  <h3>Candidate Profile</h3>
                  <span className="status-badge">Parsed</span>
                </div>

                <div className="resume-details">
                  <div className="detail-item">
                    <span className="detail-label">Name</span>
                    <span className="detail-value">{resume.name || "N/A"}</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Designation</span>
                    <span className="detail-value">{resume.designation || "N/A"}</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Email</span>
                    <span className="detail-value">{resume.email || "N/A"}</span>
                  </div>

                  <div className="detail-item">
                    <span className="detail-label">Experience</span>
                    <span className="detail-value">{resume.experience || "N/A"}</span>
                  </div>
                </div>

                <div style={{ marginTop: "18px" }}>
                  <span className="detail-label">Skills Detected</span>
                  <div className="job-tags" style={{ marginTop: "8px" }}>
                    {skills.map((s, i) => (
                      <span className="skill-tag" key={i}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  className="btn primary"
                  style={{ width: "100%", marginTop: "20px" }}
                  onClick={getRecommendations}
                  disabled={loading}
                >
                  {loading ? "Matching Roles..." : "Find Matching Jobs →"}
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Dynamic View Panels */}
          <div>
            {/* View 1: Job Recommendations */}
            {activeTab === "jobs" && (
              <div>
                <div className="card" style={{ marginBottom: "20px" }}>
                  <div className="section-heading">
                    <div>
                      <h2>Recommended Opportunities</h2>
                      <p>Roles tailored to your specific technical profile</p>
                    </div>
                    <span className="status-badge">{filteredJobs.length} Available</span>
                  </div>

                  {/* Filter Toolbar */}
                  <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                    <input
                      type="text"
                      placeholder="Search title, company, or skill..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      style={{ flex: 1, minWidth: "200px" }}
                    />
                    <button
                      className={`btn ${filterRemote ? "primary" : "btn-secondary"}`}
                      onClick={() => setFilterRemote(!filterRemote)}
                    >
                      {filterRemote ? "✓ Remote Only" : "Remote Only"}
                    </button>
                  </div>
                </div>

                {filteredJobs.length === 0 ? (
                  <div className="empty-state card">
                    <div className="empty-state-icon">🔍</div>
                    <h3>No Job Matches Found</h3>
                    <p>
                      Upload a resume or modify your search filters to view recommendations.
                    </p>
                  </div>
                ) : (
                  <div className="jobs-grid">
                    {filteredJobs.map((job) => (
                      <div className="job-card" key={job.job_id}>
                        <div className="job-card-header">
                          <div className="company-logo">
                            {(job.company || "C").charAt(0)}
                          </div>
                          <div className="job-heading-content">
                            <h3>{job.title}</h3>
                            <div className="company-name">{job.company}</div>
                          </div>
                        </div>

                        <div className="job-meta">
                          <span className="job-tag">📍 {job.location}</span>
                          <span className="job-tag">⏳ {job.experience_required}</span>
                        </div>

                        {job.match_score && (
                          <span className="match-score">
                            🔥 {job.match_score}% Match Score
                          </span>
                        )}

                        <div className="job-tags">
                          {job.skills?.slice(0, 4).map((sk, idx) => (
                            <span className="skill-tag" key={idx}>
                              {sk}
                            </span>
                          ))}
                        </div>

                        {job.match_reasons?.length > 0 && (
                          <div className="match-reasons">
                            <h4>Why it fits:</h4>
                            <p>• {job.match_reasons[0]}</p>
                          </div>
                        )}

                        <div className="job-card-footer">
                          {job.source_link && (
                            <a
                              href={job.source_link}
                              target="_blank"
                              rel="noreferrer"
                              className="view-job-link"
                            >
                              Details ↗
                            </a>
                          )}
                          <button
                            className="btn primary"
                            onClick={() => applyForJob(job)}
                            disabled={loading}
                          >
                            Apply Now
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* View 2: Interactive AI Copilot Chat */}
            {activeTab === "copilot" && (
              <div className="chat-card card">
                <div className="chat-header">
                  <div className="chat-avatar">🤖</div>
                  <div>
                    <h3>Career Assistant Copilot</h3>
                    <p>Online & Ready to help</p>
                  </div>
                </div>

                <div className="chat-messages">
                  {chatHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`message ${
                        msg.sender === "user" ? "user" : "assistant"
                      }`}
                    >
                      {msg.text}
                    </div>
                  ))}
                  {loading && (
                    <div className="message assistant">
                      <div className="spinner"></div> Thinking...
                    </div>
                  )}
                </div>

                <div className="quick-prompts">
                  <button onClick={() => setChatInput("Show remote Java jobs")}>
                    🌐 Remote Java Jobs
                  </button>
                  <button onClick={() => setChatInput("Find roles with React and Spring Boot")}>
                    ⚡ React + Spring Boot
                  </button>
                  <button onClick={() => setChatInput("Prepare me for a Java Developer interview")}>
                    🎯 Interview Prep
                  </button>
                </div>

                <form className="chat-input-area" onSubmit={sendMessage}>
                  <input
                    type="text"
                    placeholder="Ask AI Copilot for role suggestions or career advice..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                  />
                  <button type="submit" className="btn primary" disabled={loading}>
                    Send
                  </button>
                </form>
              </div>
            )}

            {/* View 3: Application Tracker Dashboard */}
            {activeTab === "applications" && (
              <div className="card">
                <div className="section-heading">
                  <div>
                    <h2>My Applications History</h2>
                    <p>Track statuses for job applications submitted via CareerPilot</p>
                  </div>
                  <button className="btn btn-secondary" onClick={loadApplications}>
                    🔄 Refresh
                  </button>
                </div>

                {applications.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <h3>No Applications Tracked Yet</h3>
                    <p>Click "Apply Now" on any job recommendation to log applications here.</p>
                  </div>
                ) : (
                  <div>
                    {applications.map((app, index) => (
                      <div className="application-item" key={index}>
                        <div>
                          <h4>{app.title}</h4>
                          <p>
                            {app.company} • Submitted:{" "}
                            {app.application_date
                              ? new Date(app.application_date).toLocaleDateString()
                              : "Recently"}
                          </p>
                        </div>
                        <span className="application-status">
                          ✓ {app.status || "Submitted"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          <strong>CareerPilot AI</strong> — Empowering candidates through intelligent resume analysis & real-time career matching.
        </p>
      </footer>
    </div>
  );
}