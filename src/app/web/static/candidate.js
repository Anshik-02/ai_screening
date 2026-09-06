/**
 * Candidate Mode Frontend Controller
 * TalentRank Studio — Guided 5-Stage Candidate Journey
 *
 * Stage 1: Setup Profile (Resume Upload / Text & Target Role)
 * Stage 2: Skill Gap Analysis & Constellation Map
 * Stage 3: Resume Improvement Recommendations
 * Stage 4: Mock Interview & Interactive Evaluation
 * Stage 5: Final Interview Readiness Report & Animated Orbit
 */

(function () {
  // ---------------------------------------------------------------------------
  // DOM References
  // ---------------------------------------------------------------------------

  // Tabs & File Inputs
  const tabTextBtn = document.getElementById("c-tab-text");
  const tabFileBtn = document.getElementById("c-tab-file");
  const resumeTextPanel = document.getElementById("c-resume-text-panel");
  const resumeFilePanel = document.getElementById("c-resume-file-panel");
  const resumeTextInput = document.getElementById("c-resume-text");
  const resumeFileInput = document.getElementById("c-resume-file-input");
  const dropZone = document.getElementById("c-drop-zone");
  const fileBadge = document.getElementById("c-file-status");
  const fileNameSpan = document.getElementById("c-file-name");
  const fileRemoveBtn = document.getElementById("c-file-remove-btn");
  const resumeCharCount = document.getElementById("c-resume-char-count");

  // Job Target & Presets
  const jobTitleInput = document.getElementById("c-job-title");
  const jobDescInput = document.getElementById("c-job-desc");
  const presetBtns = document.querySelectorAll(".btn-preset");

  // Action Buttons
  const analyzeBtn = document.getElementById("c-analyze-btn");
  const backSetupBtn = document.getElementById("c-back-setup");
  const gotoImprovementsBtn = document.getElementById("c-goto-improvements-btn");
  const backAnalysisBtn = document.getElementById("c-back-analysis");
  const gotoPrepBtn = document.getElementById("c-goto-prep-btn");
  const backImprovementsBtn = document.getElementById("c-back-improvements");
  const prepMaxQuestionsSelect = document.getElementById("c-prep-max-questions");
  const startInterviewBtn = document.getElementById("c-start-interview-btn");
  const submitAnswerBtn = document.getElementById("c-submit-answer-btn");
  const answerTextInput = document.getElementById("c-answer-text");
  const answerStatus = document.getElementById("c-answer-status");
  const restartBtn = document.getElementById("c-restart-btn");

  // Demo & Presentation Mode Controls
  const demoBtn = document.getElementById("c-demo-btn");
  const presToggleBtn = document.getElementById("c-pres-toggle");
  const restartDemoBtn = document.getElementById("c-restart-demo-btn");
  const demoExitBtn = document.getElementById("c-demo-exit-btn");
  const demoAnswerBtn = document.getElementById("c-demo-answer-btn");
  const presBar = document.getElementById("c-presentation-bar");
  const presPrevBtn = document.getElementById("c-pres-prev");
  const presNextBtn = document.getElementById("c-pres-next");
  const presStageLabel = document.getElementById("c-pres-stage-label");

  // Visual Components & Banners
  const engineStatusPill = document.getElementById("c-engine-status");
  const engineLabel = document.getElementById("c-engine-label");
  const analysisSeq = document.getElementById("c-analysis-seq");
  const llmBanner = document.getElementById("c-llm-banner");
  const llmBannerMsg = document.getElementById("c-llm-banner-msg");
  const loadingScreen = document.getElementById("c-loading-screen");
  const loadingTitle = document.getElementById("c-loading-title");
  const loadingSubtitle = document.getElementById("c-loading-subtitle");

  // Stages
  const setupStage = document.getElementById("c-setup-stage");
  const analysisStage = document.getElementById("c-analysis-stage");
  const improvementsStage = document.getElementById("c-improvements-stage");
  const prepStage = document.getElementById("c-prep-stage");
  const interviewStage = document.getElementById("c-interview-stage");
  const reportStage = document.getElementById("c-report-stage");

  // Stepper Nodes
  const stepperNodes = document.querySelectorAll(".c-step");

  // Session State
  let inputMode = "text"; // "text" | "file"
  let selectedFile = null;
  let currentAnalysisData = null;
  let currentSessionId = null;
  let activeQuestion = null;
  let currentStageNum = 1;
  let isDemoMode = false;
  let isPresentationMode = false;

  // Preset Role Data Definitions
  const ROLE_PRESETS = {
    backend: {
      title: "Senior Backend Python Engineer",
      desc: "Looking for an engineer experienced in Python, FastAPI, PostgreSQL, Docker, and AWS. Must own API performance, observability, and reliable delivery in production.",
    },
    fullstack: {
      title: "Senior Full Stack Engineer (React / Node)",
      desc: "Seeking a Full Stack Engineer proficient in React, TypeScript, Node.js, and GraphQL. Experience with modern CSS, state management, stateful web API design, and automated testing required.",
    },
    ai_engineer: {
      title: "AI / Machine Learning Systems Engineer",
      desc: "Seeking an AI Engineer with expertise in PyTorch, Python, LLM orchestration, vector databases, and model deployment on AWS/Kubernetes. High performance inference and RAG pipelines.",
    },
  };

  // Bundled Alex Rivera Demo Scenario Data
  const ALEX_RIVERA_DEMO = {
    jobTitle: "Senior Backend Engineer (Python & Distributed Systems)",
    jobDesc: "We are seeking a Senior Backend Engineer to architect high-throughput microservices using Python, FastAPI, PostgreSQL, Redis, Docker, and Kubernetes. The ideal candidate has 4+ years experience with distributed caching, RESTful API design, CI/CD, and Cloud Native deployments on AWS.",
    resumeText: `Alex Rivera
Senior Backend Software Engineer
Email: alex.rivera@example.com | GitHub: github.com/arivera | Location: Austin, TX

SUMMARY
Passionate Backend Engineer with 4.5+ years of experience designing and scaling microservices in Python, FastAPI, and Flask. Strong track record of optimizing database queries, implementing Redis caching layers, and deploying containerized applications via Docker and AWS.

SKILLS
- Languages & Frameworks: Python, FastAPI, Flask, AsyncIO, SQL, HTML/CSS
- Databases & Storage: PostgreSQL, Redis, SQLAlchemy, Database Indexing
- Cloud & DevOps: Docker, AWS (EC2, S3), Git, CI/CD (GitHub Actions), Linux
- Architecture: REST API Design, Microservices, Asynchronous Task Queues (Celery), Unit Testing (pytest)

EXPERIENCE
Senior Software Engineer | CloudScale Systems | 2022 – Present
- Architected RESTful microservices in Python/FastAPI serving over 2M daily requests with 99.95% uptime.
- Optimized PostgreSQL query execution plans and introduced Redis caching, reducing API P99 latency by 42%.
- Containerized 12 backend services using Docker and built automated CI/CD pipelines using GitHub Actions.

Backend Engineer | DataPulse Inc. | 2020 – 2022
- Developed core data ingestion pipelines in Python handling 50GB+ daily data volume.
- Implemented Celery background worker queues for asynchronous report generation.
- Designed database schemas and migration scripts using PostgreSQL and SQLAlchemy.

EDUCATION
B.S. in Computer Science | University of Texas at Austin | 2020`,
    demoAnswers: [
      "In my recent role at CloudScale Systems, we faced P99 latency spikes during peak traffic. I analyzed our PostgreSQL query plans using EXPLAIN ANALYZE and identified missing composite indexes on frequently filtered foreign keys. I also introduced a Redis caching layer for read-heavy user profile endpoints with a 5-minute TTL. This reduced database CPU utilization by 35% and improved overall P99 response time from 380ms down to 110ms.",
      "FastAPI utilizes Python's asyncio and ASGI (Asynchronous Server Gateway Interface) standard, allowing a single event loop process to handle thousands of concurrent I/O-bound requests without thread blocking. Flask, by default, is WSGI-based and synchronous, requiring multi-threading or worker processes (like Gunicorn with gevent) to handle concurrency. For microservices with high network/DB wait times, FastAPI provides significantly higher throughput.",
      "I implement database migrations using Alembic alongside SQLAlchemy. For zero-downtime deployments, I follow a strict two-phase migration pattern: first, add new nullable columns or tables, deploy the new backend code supporting both schemas, backfill data asynchronously, and finally drop deprecated fields in a subsequent release. We also run migrations automatically in our GitHub Actions CI pipeline after automated tests pass.",
      "When designing RESTful APIs, I structure endpoints around resource nouns (e.g., /api/v1/orders) using standard HTTP methods (GET, POST, PUT, DELETE). For error handling, I enforce standard status codes (400 for bad input, 401/403 for auth, 404 for missing resources, 500 for internal errors) with structured JSON payload details following RFC 7807. I also implement rate limiting via Redis token bucket algorithms.",
      "To debug performance bottlenecks, I trace request paths using OpenTelemetry and Prometheus metrics paired with Grafana dashboards. I monitor key metrics: latency (P50/P90/P99), error rates, CPU/memory usage, and DB connection pool saturation. For code-level profiling, I use cProfile and py-spy to pinpoint CPU-bound bottlenecks without restarting the service."
    ]
  };

  // ---------------------------------------------------------------------------
  // API URL Helper
  // ---------------------------------------------------------------------------
  function getApiBaseUrl() {
    const explicitBase = window.localStorage.getItem("talentrank_api_base");
    if (explicitBase) return explicitBase.replace(/\/$/, "");
    if (window.location.protocol === "file:") return "http://127.0.0.1:8001";
    return window.location.origin;
  }

  function apiUrl(path) {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${getApiBaseUrl()}${normalizedPath}`;
  }

  // ---------------------------------------------------------------------------
  // Engine Status Pill
  // ---------------------------------------------------------------------------
  async function checkEngineStatus() {
    try {
      const res = await fetch(apiUrl("/health"));
      if (res.ok) {
        const data = await res.json();
        if (data.llm_configured) {
          engineStatusPill.className = "c-engine-status ai-mode";
          engineLabel.textContent = "AI-Assisted Analysis";
        } else {
          engineStatusPill.className = "c-engine-status rule-mode";
          engineLabel.textContent = "Rule-Based Intelligence";
        }
      }
    } catch {
      engineStatusPill.className = "c-engine-status rule-mode";
      engineLabel.textContent = "Rule-Based Intelligence";
    }
  }

  // ---------------------------------------------------------------------------
  // Guided Journey Stepper & Stage Navigation (Strict 5 Stages)
  // ---------------------------------------------------------------------------
  function goToStage(stageNum) {
    hideLoading();
    currentStageNum = Math.max(1, Math.min(5, stageNum));

    // Hide all stage sections
    [setupStage, analysisStage, improvementsStage, prepStage, interviewStage, reportStage].forEach(
      (sec) => sec && sec.classList.add("hidden")
    );

    // Map stages:
    // Stage 1: Setup Profile
    // Stage 2: Skill Gap Analysis
    // Stage 3: Resume Improvements
    // Stage 4: Mock Interview (prepStage if not started, interviewStage if active)
    // Stage 5: Readiness Report & Roadmap
    if (currentStageNum === 1) setupStage?.classList.remove("hidden");
    else if (currentStageNum === 2) analysisStage?.classList.remove("hidden");
    else if (currentStageNum === 3) improvementsStage?.classList.remove("hidden");
    else if (currentStageNum === 4) {
      if (currentSessionId) interviewStage?.classList.remove("hidden");
      else prepStage?.classList.remove("hidden");
    } else if (currentStageNum === 5) {
      reportStage?.classList.remove("hidden");
      if (currentAnalysisData) {
        renderReadinessOrbit();
      }
    }

    // Scroll smoothly to content top
    window.scrollTo({ top: 120, behavior: "smooth" });

    // Update Stepper Nodes
    stepperNodes.forEach((node) => {
      const stepIdx = parseInt(node.getAttribute("data-step"), 10);
      node.classList.toggle("active", stepIdx === currentStageNum);
      node.classList.toggle("completed", stepIdx < currentStageNum);
    });

    // Update Presentation Mode Label & Buttons
    if (presStageLabel) {
      const stageTitles = ["Profile & Role", "Skill Gap", "Improvements", "Mock Interview", "Readiness Report"];
      presStageLabel.textContent = `Stage ${currentStageNum} of 5 — ${stageTitles[currentStageNum - 1]}`;
    }
    if (presPrevBtn) presPrevBtn.disabled = currentStageNum === 1;
    if (presNextBtn) presNextBtn.disabled = currentStageNum === 5;
  }

  // Stepper Node Click Navigation
  stepperNodes.forEach((node) => {
    node.addEventListener("click", () => {
      const targetStep = parseInt(node.getAttribute("data-step"), 10);
      if (targetStep === 1) goToStage(1);
      else if (targetStep === 2 && currentAnalysisData) goToStage(2);
      else if (targetStep === 3 && currentAnalysisData) goToStage(3);
      else if (targetStep === 4 && (currentAnalysisData || currentSessionId)) goToStage(4);
      else if (targetStep === 5 && currentAnalysisData) goToStage(5);
    });

    node.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        node.click();
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Demo Mode Controller (Alex Rivera Scenario)
  // ---------------------------------------------------------------------------
  function initDemoMode() {
    isDemoMode = true;
    document.body.classList.add("demo-mode-active");

    // Populate inputs with Alex Rivera data
    jobTitleInput.value = ALEX_RIVERA_DEMO.jobTitle;
    jobDescInput.value = ALEX_RIVERA_DEMO.jobDesc;
    resumeTextInput.value = ALEX_RIVERA_DEMO.resumeText;
    resumeCharCount.textContent = ALEX_RIVERA_DEMO.resumeText.length;

    // Switch to text tab
    tabTextBtn?.click();

    // Trigger profile analysis
    analyzeBtn?.click();
  }

  function exitDemoMode() {
    isDemoMode = false;
    document.body.classList.remove("demo-mode-active");
    restartBtn?.click();
  }

  demoBtn?.addEventListener("click", () => initDemoMode());
  restartDemoBtn?.addEventListener("click", () => initDemoMode());
  demoExitBtn?.addEventListener("click", () => exitDemoMode());

  // Demo Answer Button Handler (Mock Interview Stage)
  demoAnswerBtn?.addEventListener("click", () => {
    if (!ALEX_RIVERA_DEMO.demoAnswers || !ALEX_RIVERA_DEMO.demoAnswers.length) return;
    const history = document.getElementById("c-feedback-history");
    const answeredCount = history ? history.children.length : 0;
    const nextAnsIndex = answeredCount % ALEX_RIVERA_DEMO.demoAnswers.length;
    answerTextInput.value = ALEX_RIVERA_DEMO.demoAnswers[nextAnsIndex];
    answerTextInput.focus();
  });

  // ---------------------------------------------------------------------------
  // Presentation Mode Controller
  // ---------------------------------------------------------------------------
  function togglePresentationMode() {
    isPresentationMode = !isPresentationMode;
    document.body.classList.toggle("presentation-mode-on", isPresentationMode);
    presToggleBtn?.classList.toggle("active", isPresentationMode);
    presToggleBtn?.setAttribute("aria-pressed", String(isPresentationMode));

    if (isPresentationMode) {
      goToStage(1);
    }
  }

  presToggleBtn?.addEventListener("click", () => togglePresentationMode());
  presPrevBtn?.addEventListener("click", () => {
    if (currentStageNum > 1) goToStage(currentStageNum - 1);
  });
  presNextBtn?.addEventListener("click", () => {
    if (currentStageNum < 5) goToStage(currentStageNum + 1);
  });

  // Keyboard navigation for Presentation Mode (Left/Right Arrow keys when toolbar focused or presentation active)
  document.addEventListener("keydown", (e) => {
    if (!isPresentationMode) return;
    if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
    if (e.key === "ArrowLeft" && currentStageNum > 1) {
      e.preventDefault();
      goToStage(currentStageNum - 1);
    } else if (e.key === "ArrowRight" && currentStageNum < 5) {
      e.preventDefault();
      goToStage(currentStageNum + 1);
    }
  });

  // ---------------------------------------------------------------------------
  // Dynamic Hero Tagline Rotator
  // ---------------------------------------------------------------------------
  const HERO_TAGLINES = [
    "Let's find out how ready you are for your next role.",
    "Deterministic skill matching paired with adaptive AI interview coaching.",
    "Tailored resume improvements and candidate readiness reporting."
  ];
  let taglineIdx = 0;
  setInterval(() => {
    const el = document.getElementById("c-hero-dynamic");
    if (!el) return;
    taglineIdx = (taglineIdx + 1) % HERO_TAGLINES.length;
    el.style.opacity = "0";
    setTimeout(() => {
      el.textContent = HERO_TAGLINES[taglineIdx];
      el.style.opacity = "1";
    }, 400);
  }, 6000);

  // ---------------------------------------------------------------------------
  // AI Analysis Sequence Overlay
  // ---------------------------------------------------------------------------
  async function runAnalysisSequence(onComplete) {
    if (!analysisSeq) {
      if (onComplete) onComplete();
      return;
    }

    analysisSeq.classList.remove("hidden");
    const steps = analysisSeq.querySelectorAll(".c-analysis-step");

    // Reset step styles
    steps.forEach((st) => {
      st.className = "c-analysis-step";
    });

    const stepDelay = isDemoMode ? 350 : 500;

    for (let i = 0; i < steps.length; i++) {
      if (i > 0) {
        steps[i - 1].className = "c-analysis-step step-done";
      }
      steps[i].className = "c-analysis-step step-active";
      await new Promise((resolve) => setTimeout(resolve, stepDelay));
    }

    if (steps.length > 0) {
      steps[steps.length - 1].className = "c-analysis-step step-done";
    }

    await new Promise((resolve) => setTimeout(resolve, 300));
    analysisSeq.classList.add("hidden");
    if (onComplete) onComplete();
  }

  // ---------------------------------------------------------------------------
  // UI Helpers & Input Event Handlers
  // ---------------------------------------------------------------------------

  // Input Tabs
  tabTextBtn?.addEventListener("click", () => {
    inputMode = "text";
    tabTextBtn.classList.add("active");
    tabTextBtn.setAttribute("aria-selected", "true");
    tabFileBtn.classList.remove("active");
    tabFileBtn.setAttribute("aria-selected", "false");
    resumeTextPanel.classList.remove("hidden");
    resumeFilePanel.classList.add("hidden");
  });

  tabFileBtn?.addEventListener("click", () => {
    inputMode = "file";
    tabFileBtn.classList.add("active");
    tabFileBtn.setAttribute("aria-selected", "true");
    tabTextBtn.classList.remove("active");
    tabTextBtn.setAttribute("aria-selected", "false");
    resumeFilePanel.classList.remove("hidden");
    resumeTextPanel.classList.add("hidden");
  });

  // Character counter for text area
  resumeTextInput?.addEventListener("input", () => {
    resumeCharCount.textContent = resumeTextInput.value.length;
  });

  // File Upload Handlers
  dropZone?.addEventListener("click", () => resumeFileInput.click());
  resumeFileInput?.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dropZone?.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("active");
  });
  dropZone?.addEventListener("dragleave", () => dropZone.classList.remove("active"));
  dropZone?.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("active");
    if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    fileBadge.classList.remove("hidden");
    fileNameSpan.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }

  fileRemoveBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    resumeFileInput.value = "";
    fileBadge.classList.add("hidden");
  });

  // Presets Handlers
  presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const presetKey = btn.getAttribute("data-preset");
      const preset = ROLE_PRESETS[presetKey];
      if (preset) {
        jobTitleInput.value = preset.title;
        jobDescInput.value = preset.desc;
      }
    });
  });

  // Loading Screen Controller
  function showLoading(title, subtitle) {
    loadingTitle.textContent = title || "Processing...";
    loadingSubtitle.textContent = subtitle || "Please wait while AI performs computation";
    loadingScreen.classList.remove("hidden");
  }

  function hideLoading() {
    loadingScreen.classList.add("hidden");
  }

  // Banner Controller
  function updateLLMBanner(llmAvailable, llmError) {
    if (!llmAvailable) {
      llmBanner.classList.remove("hidden");
      llmBannerMsg.textContent = llmError || "AI Service Unavailable — Running in Deterministic Rule-Based Fallback Mode.";
    } else {
      llmBanner.classList.remove("hidden");
      llmBannerMsg.textContent = "AI Mode Active (OpenAI Provider). Structured JSON analysis enabled.";
    }
  }

  // ---------------------------------------------------------------------------
  // Stage Navigation Buttons
  // ---------------------------------------------------------------------------
  backSetupBtn?.addEventListener("click", () => goToStage(1));
  gotoImprovementsBtn?.addEventListener("click", () => goToStage(3));
  backAnalysisBtn?.addEventListener("click", () => goToStage(2));
  gotoPrepBtn?.addEventListener("click", () => goToStage(4));
  backImprovementsBtn?.addEventListener("click", () => goToStage(3));

  restartBtn?.addEventListener("click", () => {
    currentAnalysisData = null;
    currentSessionId = null;
    activeQuestion = null;
    document.getElementById("c-feedback-history").innerHTML = "";
    goToStage(1);
  });

  // Keyboard shortcut for submitting answer (Ctrl + Enter)
  answerTextInput?.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      submitAnswerBtn.click();
    }
  });

  // ---------------------------------------------------------------------------
  // Stage 1 -> 2: Perform Skill Gap Analysis
  // ---------------------------------------------------------------------------
  analyzeBtn?.addEventListener("click", async () => {
    const jobTitle = jobTitleInput.value.trim();
    const jobDesc = jobDescInput.value.trim();

    if (!jobTitle || !jobDesc) {
      alert("Please provide both a Job Title and Job Description.");
      return;
    }

    // Run AI analysis sequence animation
    await runAnalysisSequence(async () => {
      showLoading(
        "Analyzing Resume & Target Role...",
        "Extracting skill taxonomy and matching candidate profile..."
      );

      try {
        let response;
        if (inputMode === "file") {
          if (!selectedFile) {
            hideLoading();
            alert("Please select a resume file (PDF, DOCX, TXT).");
            return;
          }
          const formData = new FormData();
          formData.append("job_title", jobTitle);
          formData.append("job_description", jobDesc);
          formData.append("resume", selectedFile);

          response = await fetch(apiUrl("/v1/candidate/analyze-file"), {
            method: "POST",
            body: formData,
          });
        } else {
          const resumeText = resumeTextInput.value.trim();
          if (resumeText.length < 30) {
            hideLoading();
            alert("Please enter a valid resume text (at least 30 characters).");
            return;
          }
          response = await fetch(apiUrl("/v1/candidate/analyze"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              resume_text: resumeText,
              job_title: jobTitle,
              job_description: jobDesc,
            }),
          });
        }

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Analysis request failed.");
        }

        currentAnalysisData = data;
        updateLLMBanner(data.llm_available, data.llm_error);

        renderSkillGapStage(data.skill_gap);
        renderImprovementsStage(data.resume_improvement);
        renderPrepFocusTags(data.skill_gap);

        goToStage(2);
      } catch (err) {
        alert(`Analysis Error: ${err.message}`);
      } finally {
        hideLoading();
      }
    });
  });

  // Render Skill Gap Visuals & Skill Constellation (Stage 2)
  function renderSkillGapStage(gap) {
    document.getElementById("c-match-pct-val").textContent = `${gap.match_percentage}%`;
    document.getElementById("c-matched-count").textContent = `${gap.matched_skills.length} / ${gap.required_skills.length}`;
    document.getElementById("c-missing-count").textContent = gap.missing_skills.length;

    const severityBadge = document.getElementById("c-match-severity-badge");
    severityBadge.textContent = `${gap.gap_severity.toUpperCase()} GAP`;
    severityBadge.className = `badge ${gap.gap_severity === "low" ? "good" : gap.gap_severity === "moderate" ? "warn" : "bad"}`;

    document.getElementById("c-matched-cnt-badge").textContent = gap.matched_skills.length;
    document.getElementById("c-partial-cnt-badge").textContent = gap.partially_covered_skills.length;
    document.getElementById("c-missing-cnt-badge").textContent = gap.missing_skills.length;

    document.getElementById("c-matched-skills").innerHTML =
      gap.matched_skills.map((s) => `<span class="pill">${s}</span>`).join("") ||
      "<span class='pill'>None detected</span>";

    document.getElementById("c-partial-skills").innerHTML =
      gap.partially_covered_skills
        .map((s) => `<span class="pill" style="background:#fef3c7; color:#92400e; border-color:#fde68a">${s}</span>`)
        .join("") || "<span class='pill'>None detected</span>";

    document.getElementById("c-missing-skills").innerHTML =
      gap.missing_skills
        .map((s) => `<span class="pill miss">${s}</span>`)
        .join("") || "<span class='pill'>None — complete skill match!</span>";

    const narrativeBox = document.getElementById("c-narrative");
    narrativeBox.innerHTML = gap.narrative
      ? `<p>${gap.narrative}</p>`
      : "<p><em>Deterministic skill match calculated successfully. Enable OpenAI API key for full qualitative AI narrative.</em></p>";

    // Render Skill Constellation SVG Map & Mobile Card Fallback
    renderSkillConstellation(gap);
  }

  // Render Resume Improvements (Stage 3)
  function renderImprovementsStage(improvements) {
    const container = document.getElementById("c-improvements-list");
    if (!improvements || !improvements.suggestions || !improvements.suggestions.length) {
      container.innerHTML = "<p class='empty-state'>No specific improvements suggested.</p>";
      return;
    }

    container.innerHTML = improvements.suggestions
      .map(
        (item) => `
        <div class="c-improvement-card">
          <div class="c-imp-top">
            <span class="c-imp-category">${item.category}</span>
            <span class="badge ${item.priority === 'high' ? 'bad' : item.priority === 'medium' ? 'warn' : 'good'}">
              ${item.priority.toUpperCase()} PRIORITY
            </span>
          </div>
          <div class="c-imp-text">${item.suggestion}</div>
        </div>
      `
      )
      .join("");
  }

  // Render Prep Focus Tags (Stage 4)
  function renderPrepFocusTags(gap) {
    const container = document.getElementById("c-prep-focus-list");
    const focusSkills = gap.missing_skills.concat(gap.partially_covered_skills).slice(0, 8);
    if (!focusSkills.length) {
      container.innerHTML = "<span class='c-focus-tag'>Core Technical Architecture</span><span class='c-focus-tag'>System Scalability</span>";
      return;
    }
    container.innerHTML = focusSkills
      .map((skill) => `<span class="c-focus-tag">🎯 Targeted Practice: <strong>${skill}</strong></span>`)
      .join("");
  }

  // ---------------------------------------------------------------------------
  // Stage 4 -> 5: Launch Mock Interview
  // ---------------------------------------------------------------------------
  startInterviewBtn?.addEventListener("click", async () => {
    const jobTitle = jobTitleInput.value.trim();
    const jobDesc = jobDescInput.value.trim();
    const maxQ = parseInt(prepMaxQuestionsSelect.value, 10) || 5;

    let resumeText = resumeTextInput.value.trim();
    if (inputMode === "file" && selectedFile) {
      resumeText = `Uploaded Resume Document: ${selectedFile.name}`;
    }

    showLoading(
      "Generating Interview Questions...",
      "Synthesizing questions based on job description & missing skills..."
    );

    try {
      const response = await fetch(apiUrl("/v1/candidate/interview/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          job_title: jobTitle,
          job_description: jobDesc,
          max_questions: maxQ,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to start interview.");
      }

      currentSessionId = data.session_id;
      activeQuestion = data.first_question;
      updateLLMBanner(data.llm_available, data.llm_error);

      document.getElementById("c-feedback-history").innerHTML = "";
      renderCurrentQuestion(1, data.total_planned);

      goToStage(5);
    } catch (err) {
      alert(`Interview Start Error: ${err.message}`);
    } finally {
      hideLoading();
    }
  });

  function renderCurrentQuestion(qNum, totalPlanned) {
    if (!activeQuestion) return;
    document.getElementById("c-q-counter").textContent = `Q ${qNum} of ${totalPlanned}`;

    const qTypeBadge = document.getElementById("c-q-type-badge");
    qTypeBadge.textContent = activeQuestion.question_type.replace("_", " ");
    qTypeBadge.className =
      activeQuestion.question_type === "adaptive_follow_up" ? "badge warn" : "badge info";

    document.getElementById("c-q-topic").textContent = `Topic: ${activeQuestion.topic}`;
    document.getElementById("c-q-text").textContent = activeQuestion.text;
    document.getElementById("c-q-difficulty").textContent = activeQuestion.difficulty.toUpperCase();

    answerTextInput.value = "";
    answerStatus.textContent = "";
  }

  // ---------------------------------------------------------------------------
  // Answer Submission & Evaluation (Stage 5)
  // ---------------------------------------------------------------------------
  submitAnswerBtn?.addEventListener("click", async () => {
    const answer = answerTextInput.value.trim();
    if (!answer) {
      alert("Please type your technical response before submitting.");
      return;
    }

    if (!currentSessionId) {
      alert("Interview session expired. Restarting setup.");
      goToStage(1);
      return;
    }

    submitAnswerBtn.disabled = true;
    answerStatus.textContent = "Analyzing response against criteria...";

    try {
      const response = await fetch(apiUrl("/v1/candidate/interview/answer"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          answer: answer,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Answer evaluation failed.");
      }

      appendFeedbackToHistory(data.question_number, activeQuestion.text, answer, data.feedback);

      if (data.is_complete || !data.next_question) {
        answerStatus.textContent = "Interview complete! Calculating final readiness report...";
        showLoading(
          "Compiling Readiness Report...",
          "Calculating weighted performance metrics & generating roadmap..."
        );
        await fetchAndRenderSummary();
      } else {
        activeQuestion = data.next_question;
        renderCurrentQuestion(data.question_number + 1, data.total_questions);
      }
    } catch (err) {
      alert(`Answer Evaluation Error: ${err.message}`);
    } finally {
      submitAnswerBtn.disabled = false;
      answerStatus.textContent = "";
    }
  });

  function appendFeedbackToHistory(qNum, qText, userAns, feedback) {
    const history = document.getElementById("c-feedback-history");
    const card = document.createElement("article");
    card.className = "c-feedback-card reveal";

    const s = feedback.scores;
    card.innerHTML = `
      <div class="panel-header-with-badge">
        <span class="badge info">QUESTION ${qNum} EVALUATION</span>
        <span class="badge ${s.overall_answer_score >= 70 ? 'good' : s.overall_answer_score >= 50 ? 'warn' : 'bad'}">
          Overall: ${s.overall_answer_score}/100
        </span>
      </div>
      <h4 style="margin:6px 0 10px; font-size:16px">${qText}</h4>
      <p style="font-size:13px; color:var(--muted); margin:0 0 12px; background:#f8fafc; padding:10px; border-radius:8px">
        <strong>Your Submission:</strong> ${userAns}
      </p>

      <div class="c-feedback-scores">
        <div class="c-score-mini"><div class="c-score-mini-val">${s.overall_answer_score}</div><div class="c-score-mini-lbl">Overall</div></div>
        <div class="c-score-mini"><div class="c-score-mini-val">${s.technical_accuracy}</div><div class="c-score-mini-lbl">Accuracy</div></div>
        <div class="c-score-mini"><div class="c-score-mini-val">${s.relevance}</div><div class="c-score-mini-lbl">Relevance</div></div>
        <div class="c-score-mini"><div class="c-score-mini-val">${s.completeness}</div><div class="c-score-mini-lbl">Completeness</div></div>
        <div class="c-score-mini"><div class="c-score-mini-val">${s.communication_clarity}</div><div class="c-score-mini-lbl">Clarity</div></div>
      </div>

      <div style="font-size:13px; display:grid; gap:6px; margin-top:10px">
        <div><strong style="color:var(--ok)">✓ Strengths:</strong> ${(feedback.strengths || []).join(" | ") || "Good effort"}</div>
        <div><strong style="color:var(--bad)">⚠ Areas for Growth:</strong> ${(feedback.weaknesses || []).join(" | ") || "None highlighted"}</div>
        ${
          feedback.improved_answer_example
            ? `<div style="margin-top:8px; padding:10px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px"><strong>💡 AI Model Answer Structure:</strong><br>${feedback.improved_answer_example}</div>`
            : ""
        }
      </div>
    `;

    history.prepend(card);
  }

  // ---------------------------------------------------------------------------
  // Stage 6: Final Readiness Report & Preparation Roadmap
  // ---------------------------------------------------------------------------
  async function fetchAndRenderSummary() {
    try {
      const response = await fetch(
        apiUrl(`/v1/candidate/interview/${currentSessionId}/summary`)
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to retrieve interview summary.");
      }

      renderReportStage(data);
      currentSessionId = null; // Mark completed
      goToStage(6);
    } catch (err) {
      alert(`Report Error: ${err.message}`);
    } finally {
      hideLoading();
    }
  }

  function renderReportStage(data) {
    const score = Math.round(data.readiness_score);
    document.getElementById("c-gauge-score").textContent = `${score}/100`;
    document.getElementById("c-gauge-band").textContent = (data.readiness_band || "Ready").replace("_", " ");

    const dash = (score / 100) * 283;
    document.getElementById("c-gauge-path").setAttribute("stroke-dasharray", `${dash} 283`);

    const b = data.score_breakdown || {};
    const perfDisplay = b.interview_performance_score !== null && b.interview_performance_score !== undefined
      ? `<strong>${b.interview_performance_score}</strong>`
      : `<span style="color:var(--muted); font-size:12px">N/A (Pending Interview)</span>`;
    const perfFillWidth = b.interview_performance_score !== null && b.interview_performance_score !== undefined
      ? b.interview_performance_score
      : 0;

    document.getElementById("c-score-breakdown").innerHTML = `
      <div class="score-row"><span>Skill Coverage (25%)</span><div class="score-bar"><div class="score-fill" style="width:${b.skill_coverage_score}%"></div></div><strong>${b.skill_coverage_score}</strong></div>
      <div class="score-row"><span>Resume Match (25%)</span><div class="score-bar"><div class="score-fill" style="width:${b.resume_job_match_score}%"></div></div><strong>${b.resume_job_match_score}</strong></div>
      <div class="score-row"><span>Interview Performance (35%)</span><div class="score-bar"><div class="score-fill" style="width:${perfFillWidth}%"></div></div>${perfDisplay}</div>
      <div class="score-row"><span>Experience Score (15%)</span><div class="score-bar"><div class="score-fill" style="width:${b.experience_score}%"></div></div><strong>${b.experience_score}</strong></div>
      ${data.status_message ? `<div style="margin-top:12px; padding:10px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; font-size:12px; color:#1e40af">💡 <strong>Assessment Note:</strong> ${data.status_message}</div>` : ''}
    `;

    const narrativeCard = document.getElementById("c-narrative-card");
    if (data.narrative) {
      narrativeCard.classList.remove("hidden");
      document.getElementById("c-report-narrative").textContent = data.narrative;
    } else {
      narrativeCard.classList.add("hidden");
    }

    const roadmapContainer = document.getElementById("c-roadmap");
    if (!data.preparation_roadmap || !data.preparation_roadmap.length) {
      roadmapContainer.innerHTML = "<p class='empty-state'>No roadmap generated.</p>";
      return;
    }

    roadmapContainer.innerHTML = `
      <div class="c-roadmap-timeline">
        ${data.preparation_roadmap
          .map(
            (item) => `
          <div class="c-roadmap-item">
            <div class="c-roadmap-pri">${item.priority}</div>
            <div class="c-roadmap-content">
              <div class="flex-between">
                <h4>${item.action}</h4>
                <span class="c-roadmap-timeline-badge">⏱ ${item.timeline}</span>
              </div>
              <p>Category: <strong>${item.category}</strong></p>
            </div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  // ---------------------------------------------------------------------------
  // Export Readiness Report Generator (Client-Side Standalone Download)
  // ---------------------------------------------------------------------------
  let lastSummaryData = null; // store last summary data for export

  const exportReportBtn = document.getElementById("c-export-report-btn");
  const exportPartialBtn = document.getElementById("c-export-partial-btn");

  exportReportBtn?.addEventListener("click", () => exportReadinessReport(false));
  exportPartialBtn?.addEventListener("click", () => exportReadinessReport(true));

  // Override renderReportStage to store lastSummaryData
  const originalRenderReportStage = renderReportStage;
  renderReportStage = function(data) {
    lastSummaryData = data;
    originalRenderReportStage(data);
  };

  function exportReadinessReport(isPartial) {
    const jobTitle = jobTitleInput?.value.trim() || "Target Role";
    const jobDesc = jobDescInput?.value.trim() || "N/A";
    const profileSummary = inputMode === "file" && selectedFile
      ? `Uploaded File: ${selectedFile.name}`
      : (resumeTextInput?.value.trim().substring(0, 300) + "..." || "Candidate Resume Provided");

    const gap = currentAnalysisData?.skill_gap || {
      match_percentage: 0,
      matched_skills: [],
      missing_skills: [],
      partially_covered_skills: [],
      gap_severity: "N/A",
      narrative: null
    };

    const improvements = currentAnalysisData?.resume_improvement?.suggestions || [];
    const summary = !isPartial ? lastSummaryData : null;
    const isInterviewDone = summary && summary.questions_answered > 0;
    const isComplete = summary && summary.is_complete;

    let readinessScore = 0;
    let readinessBandLabel = "";
    let formulaExplanationText = "";
    let assessmentStatusBadge = "";

    if (summary) {
      readinessScore = Math.round(summary.readiness_score);
      formulaExplanationText = summary.status_message || summary.score_breakdown?.formula_explanation || "";
      if (summary.assessment_status === "final") {
        readinessBandLabel = summary.readiness_band.replace("_", " ").toUpperCase();
        assessmentStatusBadge = "badge-good";
      } else if (summary.assessment_status === "in_progress") {
        readinessBandLabel = `IN-PROGRESS ASSESSMENT (${summary.questions_answered} Qs Answered)`;
        assessmentStatusBadge = "badge-warn";
      } else {
        readinessBandLabel = "PRELIMINARY PROFILE ASSESSMENT (NO INTERVIEW)";
        assessmentStatusBadge = "badge-warn";
      }
    } else {
      // Stage 2 export without session
      const expScore = 70.0; // standard 3-year baseline or default
      const cov = gap.match_percentage || 0;
      readinessScore = Math.round((0.25 * cov + 0.25 * cov + 0.15 * expScore) / 0.65);
      readinessBandLabel = "PRELIMINARY PROFILE ASSESSMENT (NO INTERVIEW)";
      assessmentStatusBadge = "badge-warn";
      formulaExplanationText = "Preliminary Profile Assessment: Normalized from available profile components (Skill Coverage 25% + Resume Match 25% + Experience 15%) / 0.65. Complete the mock interview to unlock your full readiness score.";
    }

    const dimAvg = summary?.dimension_averages || {};

    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TalentRank Studio — Interview Readiness Report</title>
  <style>
    :root {
      --primary: #0284c7;
      --primary-dark: #0369a1;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --muted: #64748b;
      --border: #e2e8f0;
      --ok: #16a34a;
      --warn: #d97706;
      --bad: #dc2626;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      margin: 0;
      padding: 30px;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
      background: var(--card-bg);
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 36px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--border);
      padding-bottom: 20px;
      margin-bottom: 24px;
    }
    .brand { font-size: 24px; font-weight: 800; color: var(--primary-dark); }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .badge-good { background: #dcfce7; color: var(--ok); }
    .badge-warn { background: #fef3c7; color: var(--warn); }
    .badge-info { background: #e0f2fe; color: var(--primary-dark); }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
    .card { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
    .card h3 { margin-top: 0; font-size: 16px; color: var(--primary-dark); }
    .score-hero { text-align: center; background: #f0f9ff; border: 2px solid #bae6fd; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
    .score-number { font-size: 48px; font-weight: 900; color: var(--primary-dark); }
    .disclaimer { font-size: 12px; color: var(--muted); font-style: italic; margin-top: 8px; }
    .pill { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; margin: 2px; }
    .pill-matched { background: #dcfce7; color: var(--ok); border: 1px solid #bbf7d0; }
    .pill-missing { background: #fee2e2; color: var(--bad); border: 1px solid #fecaca; }
    .formula-box { background: #fffbebf5; border: 1px solid #fde68a; border-radius: 8px; padding: 14px; font-size: 13px; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
    th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
    th { background: #f1f5f9; font-weight: 600; }
    .btn-print {
      background: var(--primary);
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      float: right;
    }
    @media print {
      .btn-print { display: none; }
      body { padding: 0; background: white; }
      .container { border: none; box-shadow: none; padding: 0; }
    }
  </style>
</head>
<body>
  <div class="container">
    <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>

    <div class="header">
      <div>
        <div class="brand">TalentRank Studio</div>
        <div style="font-size:14px; color:var(--muted)">Interview Readiness Report</div>
      </div>
      <div>
        <span class="badge ${assessmentStatusBadge}">${readinessBandLabel}</span>
      </div>
    </div>

    <!-- Profile & Job Summary -->
    <div class="grid">
      <div class="card">
        <h3>👤 Candidate Profile Summary</h3>
        <p style="font-size:13px; color:var(--text); margin:0">${profileSummary}</p>
      </div>
      <div class="card">
        <h3>🎯 Target Job Title</h3>
        <p style="font-size:14px; font-weight:700; color:var(--primary-dark); margin:0">${jobTitle}</p>
        <p style="font-size:12px; color:var(--muted); margin-top:4px">${jobDesc.substring(0, 150)}...</p>
      </div>
    </div>

    <!-- Readiness Score Hero Card -->
    <div class="score-hero">
      <div style="font-size:14px; font-weight:700; color:var(--muted)">
        ${isInterviewDone && isComplete ? 'OVERALL INTERVIEW READINESS SCORE' : 'PRELIMINARY INTERVIEW READINESS SCORE'}
      </div>
      <div class="score-number">${readinessScore}/100</div>
      <div style="font-weight:700; color:var(--primary-dark)">Assessment Status: ${readinessBandLabel}</div>
      <p class="disclaimer">⚠️ Disclaimer: All scores are AI/rule-generated estimates intended for professional development and interview practice guidance.</p>
    </div>

    <!-- Formula Explanation -->
    <div class="formula-box">
      <strong>📐 Deterministic Readiness Formula & Assessment Status:</strong><br>
      ${formulaExplanationText || 'Overall Score = Skill Coverage (25%) + Resume Match (25%) + Mock Interview Performance (35%) + Years Experience (15%)'}
    </div>

    <!-- Score Breakdown Table -->
    <div class="card" style="margin-bottom:24px">
      <h3>📊 Score Breakdown</h3>
      <table>
        <thead>
          <tr><th>Component</th><th>Weight</th><th>Calculated Score</th></tr>
        </thead>
        <tbody>
          <tr><td>Skill Coverage</td><td>25%</td><td>${summary ? summary.score_breakdown.skill_coverage_score : gap.match_percentage}/100</td></tr>
          <tr><td>Resume-Job Match</td><td>25%</td><td>${summary ? summary.score_breakdown.resume_job_match_score : gap.match_percentage}/100</td></tr>
          <tr>
            <td>Mock Interview Performance</td>
            <td>35%</td>
            <td>${summary && summary.score_breakdown.interview_performance_score !== null && summary.score_breakdown.interview_performance_score !== undefined ? `${summary.score_breakdown.interview_performance_score}/100` : '<em>N/A — Pending Mock Interview</em>'}</td>
          </tr>
          <tr><td>Experience Score</td><td>15%</td><td>${summary ? summary.score_breakdown.experience_score : 70}/100</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Skill Taxonomy Analysis -->
    <div class="grid">
      <div class="card">
        <h3>✅ Matched Skills (${gap.matched_skills.length})</h3>
        <div>${gap.matched_skills.map(s => `<span class="pill pill-matched">${s}</span>`).join('') || 'None detected'}</div>
      </div>
      <div class="card">
        <h3>❌ Critical Skill Gaps (${gap.missing_skills.length})</h3>
        <div>${gap.missing_skills.map(s => `<span class="pill pill-missing">${s}</span>`).join('') || 'None — full match!'}</div>
      </div>
    </div>

    <!-- Resume Improvement Priorities -->
    <div class="card" style="margin-bottom:24px">
      <h3>💡 Prioritized Resume Improvements</h3>
      <ul style="padding-left:20px; font-size:13px; margin:0">
        ${improvements.map(imp => `<li><strong>[${imp.priority.toUpperCase()}] ${imp.category}:</strong> ${imp.suggestion}</li>`).join('') || '<li>No specific resume improvements listed.</li>'}
      </ul>
    </div>

    <!-- Mock Interview Performance Summary -->
    <div class="card" style="margin-bottom:24px">
      <h3>🎙️ Mock Interview Performance Summary</h3>
      ${isInterviewDone ? `
        <p style="font-size:13px"><strong>Questions Answered:</strong> ${summary.questions_answered} | <strong>Average Answer Score:</strong> ${summary.average_answer_score}/100</p>
        <h4 style="font-size:13px; margin-top:12px; margin-bottom:6px">Five Evaluation Dimension Averages:</h4>
        <table>
          <thead>
            <tr><th>Technical Accuracy</th><th>Relevance</th><th>Completeness</th><th>Communication Clarity</th><th>Answer Structure</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>${dimAvg.technical_accuracy ?? 'N/A'}/100</td>
              <td>${dimAvg.relevance ?? 'N/A'}/100</td>
              <td>${dimAvg.completeness ?? 'N/A'}/100</td>
              <td>${dimAvg.communication_clarity ?? 'N/A'}/100</td>
              <td>${dimAvg.answer_structure ?? 'N/A'}/100</td>
            </tr>
          </tbody>
        </table>
      ` : `
        <div style="padding:12px; background:#fef3c7; border:1px solid #fde68a; border-radius:6px; color:#92400e; font-size:13px">
          ⚠️ <strong>Mock Interview Status: Not Completed / Unavailable</strong><br>
          The candidate has not completed the interactive mock interview for this session. Complete Stage 5 to unlock your full 100% weighted readiness report.
        </div>
      `}
    </div>

    <!-- Preparation Roadmap -->
    <div class="card">
      <h3>🗺️ Actionable Preparation Roadmap</h3>
      <ol style="padding-left:20px; font-size:13px; margin:0">
        ${(summary?.preparation_roadmap || [
          { priority: 1, action: "Address missing technical skills identified in taxonomy analysis.", timeline: "2-4 weeks" },
          { priority: 2, action: "Tailor resume phrasing to match exact job description keywords.", timeline: "1 week" },
          { priority: 3, action: "Complete mock interview session to practice technical communication.", timeline: "Immediate" }
        ]).map(item => `<li><strong>${item.action}</strong> (Timeline: ${item.timeline})</li>`).join('')}
      </ol>
    </div>

    <div style="text-align:center; font-size:11px; color:var(--muted); margin-top:30px; border-top:1px solid var(--border); padding-top:14px">
      Report Generated by TalentRank Studio — AI Resume & Interview Coaching System.<br>
      Session data is stateless and ephemeral. No personal data was saved to a database.
    </div>

  </div>
</body>
</html>`;

    // Trigger download of HTML report file
    const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const downloadLink = document.createElement("a");
    const safeTitle = jobTitle.replace(/[^a-z0-9]/gi, "_").toLowerCase();
    downloadLink.href = url;
    downloadLink.download = `TalentRank_Interview_Readiness_Report_${safeTitle}.html`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(url);
  }

  // ---------------------------------------------------------------------------
  // Skill Constellation Interactive Map Visualizer (Stage 2)
  // ---------------------------------------------------------------------------
  function renderSkillConstellation(gap) {
    const container = document.getElementById("c-constellation-map");
    if (!container) return;

    const matched = gap.matched_skills || [];
    const partial = gap.partially_covered_skills || [];
    const missing = gap.missing_skills || [];

    const allSkills = [
      ...matched.map((s) => ({ name: s, type: "matched", color: "#10b981" })),
      ...partial.map((s) => ({ name: s, type: "partial", color: "#f59e0b" })),
      ...missing.map((s) => ({ name: s, type: "missing", color: "#ef4444" })),
    ];

    if (!allSkills.length) {
      container.innerHTML = "<p class='empty-state'>No skill nodes available for constellation.</p>";
      return;
    }

    const width = 600;
    const height = 280;
    const centerX = width / 2;
    const centerY = height / 2;

    let svgNodes = [];
    let svgLines = [];
    const nodeCount = allSkills.length;
    const radius = Math.min(width, height) * 0.35;

    allSkills.forEach((skill, idx) => {
      const angle = (idx / nodeCount) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      // Line connecting center node to skill node
      svgLines.push(`
        <line x1="${centerX}" y1="${centerY}" x2="${x}" y2="${y}" stroke="${skill.color}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="3 3" />
      `);

      // Node circle + text label
      svgNodes.push(`
        <g class="constellation-node" tabindex="0" role="button" aria-label="${skill.type}: ${skill.name}">
          <circle cx="${x}" cy="${y}" r="8" fill="${skill.color}" filter="drop-shadow(0 0 6px ${skill.color})" />
          <circle cx="${x}" cy="${y}" r="14" fill="none" stroke="${skill.color}" stroke-opacity="0.4" stroke-width="1" />
          <text x="${x}" y="${y + 22}" fill="#e2e8f0" font-size="11" font-weight="600" text-anchor="middle">${skill.name}</text>
        </g>
      `);
    });

    // Center Core Node (Target Role)
    const centerNodeHtml = `
      <g class="constellation-node-core">
        <circle cx="${centerX}" cy="${centerY}" r="22" fill="#0284c7" filter="drop-shadow(0 0 12px #0284c7)" />
        <circle cx="${centerX}" cy="${centerY}" r="30" fill="none" stroke="#38bdf8" stroke-opacity="0.5" stroke-width="1.5" />
        <text x="${centerX}" y="${centerY + 4}" fill="#ffffff" font-size="10" font-weight="800" text-anchor="middle">TARGET ROLE</text>
      </g>
    `;

    container.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" class="c-constellation-svg" aria-label="Skill Constellation Map">
        <defs>
          <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#0284c7" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#0f172a" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <circle cx="${centerX}" cy="${centerY}" r="${radius + 20}" fill="url(#coreGlow)" />
        ${svgLines.join("")}
        ${svgNodes.join("")}
        ${centerNodeHtml}
      </svg>
    `;
  }

  // ---------------------------------------------------------------------------
  // Readiness Orbit Animated Visualizer (Stage 5)
  // ---------------------------------------------------------------------------
  function renderReadinessOrbit() {
    const scoreValEl = document.getElementById("c-orbit-score-val");
    const statusValEl = document.getElementById("c-orbit-status-val");
    const fillCircle = document.getElementById("c-orbit-circle-fill");

    if (!scoreValEl || !fillCircle) return;

    let score = 0;
    let isPreliminary = true;

    if (lastSummaryData) {
      score = Math.round(lastSummaryData.readiness_score || 0);
      isPreliminary = lastSummaryData.assessment_status !== "final";
    } else if (currentAnalysisData?.skill_gap) {
      const gap = currentAnalysisData.skill_gap;
      const expScore = 70.0;
      const cov = gap.match_percentage || 0;
      score = Math.round((0.25 * cov + 0.25 * cov + 0.15 * expScore) / 0.65);
      isPreliminary = true;
    }

    scoreValEl.textContent = score;

    if (statusValEl) {
      if (isPreliminary) {
        statusValEl.textContent = "PRELIMINARY ASSESSMENT";
        statusValEl.style.color = "var(--warn)";
      } else {
        statusValEl.textContent = "FINAL READINESS SCORE";
        statusValEl.style.color = "var(--good)";
      }
    }

    // Circumference for r=110 SVG circle is ~691
    const circumference = 2 * Math.PI * 110;
    const strokeDashoffset = circumference - (score / 100) * circumference;
    fillCircle.style.strokeDasharray = `${circumference}`;
    fillCircle.style.strokeDashoffset = `${strokeDashoffset}`;
  }

  // Initialize Engine Status Pill on load
  checkEngineStatus();

})();


