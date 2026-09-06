const candidateList = document.getElementById("candidate-list");
const candidateTemplate = document.getElementById("candidate-template");
const analysisForm = document.getElementById("analysis-form");
const leaderboard = document.getElementById("leaderboard");
const statusBanner = document.getElementById("status-banner");
const resultSubtitle = document.getElementById("result-subtitle");
const compareA = document.getElementById("compare-a");
const compareB = document.getElementById("compare-b");
const comparisonContent = document.getElementById("comparison-content");
const addCandidateButton = document.getElementById("add-candidate");
const textModeSection = document.getElementById("text-mode-section");
const fileModeSection = document.getElementById("file-mode-section");
const resumeFilesInput = document.getElementById("resume-files");
const dropZone = document.getElementById("drop-zone");
const uploadPreview = document.getElementById("upload-preview");
const previewStatus = document.getElementById("preview-status");
const profilePreviewCards = document.getElementById("profile-preview-cards");
const modeInputs = Array.from(document.querySelectorAll('input[name="analysis-mode"]'));

let latestCandidates = [];
let selectedFiles = [];
const DEFAULT_API_BASE = "http://127.0.0.1:8001";

function getApiBaseUrl() {
  const explicitBase = window.localStorage.getItem("talentrank_api_base");
  if (explicitBase) {
    return explicitBase.replace(/\/$/, "");
  }

  if (window.location.protocol === "file:") {
    return DEFAULT_API_BASE;
  }

  return window.location.origin;
}

function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

function getAnalysisMode() {
  const selected = modeInputs.find((input) => input.checked);
  return selected ? selected.value : "text";
}

function updateModeVisibility() {
  const mode = getAnalysisMode();
  const isTextMode = mode === "text";

  textModeSection.classList.toggle("hidden-mode", !isTextMode);
  fileModeSection.classList.toggle("hidden-mode", isTextMode);
  addCandidateButton.classList.toggle("hidden-mode", !isTextMode);
}

function updateUploadPreview() {
  if (!selectedFiles.length) {
    uploadPreview.className = "upload-preview empty-state";
    uploadPreview.innerHTML = "<p>No files selected.</p>";
    profilePreviewCards.className = "profile-preview-cards empty-state";
    profilePreviewCards.innerHTML = "<p>Parsed profile previews will appear here.</p>";
    previewStatus.classList.add("hidden");
    return;
  }

  uploadPreview.className = "upload-preview";
  uploadPreview.innerHTML = `
    <p><strong>${selectedFiles.length}</strong> file(s) selected</p>
    <ul>${selectedFiles.map((file) => `<li>${file.name}</li>`).join("")}</ul>
  `;
}

function syncInputWithSelectedFiles() {
  const transfer = new DataTransfer();
  selectedFiles.forEach((file) => transfer.items.add(file));
  resumeFilesInput.files = transfer.files;
}

function setSelectedFiles(files) {
  selectedFiles = files;
  syncInputWithSelectedFiles();
  updateUploadPreview();
  void fetchUploadPreviews();
}

function renderProfilePreviews(previews) {
  if (!previews.length) {
    profilePreviewCards.className = "profile-preview-cards empty-state";
    profilePreviewCards.innerHTML = "<p>Parsed profile previews will appear here.</p>";
    return;
  }

  profilePreviewCards.className = "profile-preview-cards";
  profilePreviewCards.innerHTML = previews
    .map((preview) => {
      if (preview.status === "error") {
        return `
          <article class="profile-card error">
            <h4>${preview.file_name}</h4>
            <p class="profile-meta">Status: parse failed</p>
            <p>${preview.message || "Could not parse this file."}</p>
          </article>
        `;
      }

      const skills = (preview.detected_skills || []).map((skill) => `<span class="pill">${skill}</span>`).join("");
      return `
        <article class="profile-card">
          <h4>${preview.candidate_name || preview.file_name}</h4>
          <p class="profile-meta">${preview.file_name} | ${preview.years_experience ?? 0} years detected</p>
          <div class="pill-row">${skills || "<span class='pill'>No skill keywords detected</span>"}</div>
        </article>
      `;
    })
    .join("");
}

async function fetchUploadPreviews() {
  if (!selectedFiles.length) {
    return;
  }

  previewStatus.classList.remove("hidden");
  previewStatus.textContent = "Parsing uploaded resumes...";

  const formData = new FormData();
  selectedFiles.forEach((file) => {
    formData.append("resumes", file, file.name);
  });

  try {
    const response = await fetch(apiUrl("/v1/preview-files"), {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Preview parsing failed");
    }

    renderProfilePreviews(data.previews || []);
    previewStatus.textContent = "Preview ready. Parsed candidate profiles from uploaded resumes.";
  } catch (error) {
    profilePreviewCards.className = "profile-preview-cards empty-state";
    profilePreviewCards.innerHTML = "<p>Unable to parse preview right now.</p>";
    const message = error && error.message ? error.message : String(error);
    previewStatus.textContent = `Preview error: ${message}`;
  }
}

function splitCommaValues(value) {
  return value
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function addCandidate(data = {}) {
  const clone = candidateTemplate.content.cloneNode(true);
  const item = clone.querySelector(".candidate-item");

  item.querySelector(".candidate-name").value = data.name || "";
  item.querySelector(".candidate-years").value = data.years_experience || "";
  item.querySelector(".candidate-resume").value = data.resume_text || "";

  item.querySelector(".remove-candidate").addEventListener("click", () => {
    item.remove();
  });

  candidateList.appendChild(clone);
}

function collectCandidates() {
  const items = Array.from(candidateList.querySelectorAll(".candidate-item"));

  return items.map((item) => ({
    name: item.querySelector(".candidate-name").value.trim(),
    years_experience: Number(item.querySelector(".candidate-years").value || 0),
    resume_text: item.querySelector(".candidate-resume").value.trim(),
  }));
}

function collectFormContext() {
  return {
    jobTitle: document.getElementById("job-title").value.trim(),
    roleFamily: document.getElementById("role-family").value,
    jobDescription: document.getElementById("job-description").value.trim(),
    mustHaveInput: document.getElementById("must-have").value,
    niceToHaveInput: document.getElementById("nice-to-have").value,
  };
}

function validateTextCandidates(candidates) {
  if (!candidates.length) {
    return "Add at least one candidate.";
  }

  const hasInvalidCandidate = candidates.some(
    (candidate) => !candidate.name || !candidate.resume_text
  );
  if (hasInvalidCandidate) {
    return "Please provide complete data for all text candidates.";
  }

  return null;
}

function validateFileCandidates(files) {
  if (!files.length) {
    return "Upload at least one resume file.";
  }

  return null;
}

async function runTextAnalysis(context) {
  const payload = {
    job_title: context.jobTitle,
    role_family: context.roleFamily,
    job_description: context.jobDescription,
    must_have_skills: splitCommaValues(context.mustHaveInput),
    nice_to_have_skills: splitCommaValues(context.niceToHaveInput),
    candidates: collectCandidates(),
  };

  const validationError = validateTextCandidates(payload.candidates);
  if (validationError) {
    throw new Error(validationError);
  }

  return fetch(apiUrl("/v1/analyze"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

async function runFileAnalysis(context) {
  const validationError = validateFileCandidates(selectedFiles);
  if (validationError) {
    throw new Error(validationError);
  }

  const formData = new FormData();
  formData.append("job_title", context.jobTitle);
  formData.append("role_family", context.roleFamily);
  formData.append("job_description", context.jobDescription);
  formData.append("must_have_skills", context.mustHaveInput);
  formData.append("nice_to_have_skills", context.niceToHaveInput);

  selectedFiles.forEach((file) => {
    formData.append("resumes", file, file.name);
  });

  return fetch(apiUrl("/v1/analyze-files"), {
    method: "POST",
    body: formData,
  });
}

function setStatus(type, message) {
  statusBanner.classList.remove("hidden", "success", "error");
  statusBanner.classList.add(type === "error" ? "error" : "success");
  statusBanner.textContent = message;
}

function scoreBar(label, value) {
  const safe = Math.max(0, Math.min(100, value));
  return `
    <div class="score-row">
      <span>${label}</span>
      <div class="score-bar"><div class="score-fill" style="width: ${safe}%"></div></div>
      <strong>${safe.toFixed(1)}</strong>
    </div>
  `;
}

function renderLeaderboard(candidates) {
  if (!candidates.length) {
    leaderboard.className = "leaderboard empty-state";
    leaderboard.innerHTML = "<p>No candidates returned from analysis.</p>";
    return;
  }

  leaderboard.className = "leaderboard";
  leaderboard.innerHTML = candidates
    .map((candidate, index) => {
      const hardClass = candidate.hard_constraint_passed ? "good" : "warn";
      const hardLabel = candidate.hard_constraint_passed ? "Hard Constraint Passed" : "Hard Constraint Risk";

      return `
        <article class="candidate-card" style="animation-delay:${index * 80}ms">
          <div class="candidate-top">
            <h3>${candidate.name}</h3>
            <span class="badge ${hardClass}">${hardLabel}</span>
          </div>
          ${scoreBar("Total", candidate.total_score)}
          ${scoreBar("Required Skill", candidate.skill_score)}
          ${scoreBar("Must-Have", candidate.must_have_match_rate)}
          ${scoreBar("Nice-To-Have", candidate.nice_to_have_match_rate)}
          ${scoreBar("Experience", candidate.experience_score)}
          <div>
            <strong>Matched Skills:</strong>
            <div class="pill-row">${candidate.matched_skills.map((skill) => `<span class="pill">${skill}</span>`).join("") || "<span class='pill'>none</span>"}</div>
          </div>
          <div>
            <strong>Missing Skills:</strong>
            <div class="pill-row">${candidate.missing_skills.map((skill) => `<span class="pill miss">${skill}</span>`).join("") || "<span class='pill'>none</span>"}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function fillComparisonSelects(candidates) {
  latestCandidates = candidates;
  const options = candidates
    .map((candidate, idx) => `<option value="${idx}">${candidate.name}</option>`)
    .join("");

  compareA.innerHTML = options;
  compareB.innerHTML = options;

  if (candidates.length > 1) {
    compareA.value = "0";
    compareB.value = "1";
  }

  renderComparison();
}

function compareCard(candidate) {
  const semanticRows = Object.entries(candidate.semantic_matches || {})
    .map(([target, support]) => `<li>${target}: ${support.join(", ")}</li>`)
    .join("");

  return `
    <article class="compare-card">
      <h4>${candidate.name}</h4>
      ${scoreBar("Total", candidate.total_score)}
      ${scoreBar("Skill", candidate.skill_score)}
      ${scoreBar("Must-Have", candidate.must_have_match_rate)}
      <p><strong>Strengths:</strong> ${(candidate.strengths || []).join(" | ") || "None"}</p>
      <p><strong>Concerns:</strong> ${(candidate.concerns || []).join(" | ") || "None"}</p>
      <p><strong>Semantic Evidence:</strong></p>
      <ul>${semanticRows || "<li>None</li>"}</ul>
    </article>
  `;
}

function renderComparison() {
  if (latestCandidates.length < 2) {
    comparisonContent.className = "comparison-content empty-state";
    comparisonContent.innerHTML = "<p>Add at least 2 candidates to compare.</p>";
    return;
  }

  const a = latestCandidates[Number(compareA.value)];
  const b = latestCandidates[Number(compareB.value)];

  if (!a || !b) {
    return;
  }

  comparisonContent.className = "comparison-content";
  comparisonContent.innerHTML = `<div class="compare-grid">${compareCard(a)}${compareCard(b)}</div>`;
}

addCandidateButton.addEventListener("click", () => addCandidate());
compareA.addEventListener("change", renderComparison);
compareB.addEventListener("change", renderComparison);
modeInputs.forEach((modeInput) => {
  modeInput.addEventListener("change", updateModeVisibility);
});
resumeFilesInput.addEventListener("change", () => {
  setSelectedFiles(Array.from(resumeFilesInput.files || []));
});

dropZone.addEventListener("click", () => {
  resumeFilesInput.click();
});

dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    resumeFilesInput.click();
  }
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("active");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("active");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("active");
  const files = Array.from(event.dataTransfer?.files || []);
  if (!files.length) {
    return;
  }
  setSelectedFiles(files);
});

analysisForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  setStatus("success", "Running analysis...");

  try {
    const mode = getAnalysisMode();
    const context = collectFormContext();
    const response = mode === "files"
      ? await runFileAnalysis(context)
      : await runTextAnalysis(context);

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Analysis request failed");
    }

    resultSubtitle.textContent = `${data.job_title} | role profile: ${data.role_family}`;
    renderLeaderboard(data.ranked_candidates || []);
    fillComparisonSelects(data.ranked_candidates || []);
    setStatus("success", "Analysis complete. Leaderboard refreshed.");
  } catch (error) {
    const baseMessage = error && error.message ? error.message : String(error);
    if (baseMessage.toLowerCase().includes("failed to fetch")) {
      setStatus(
        "error",
        "Error: Failed to reach API. Start backend with uvicorn and open dashboard at the same origin or set localStorage talentrank_api_base."
      );
      return;
    }

    setStatus("error", `Error: ${baseMessage}`);
  }
});

addCandidate({
  name: "Aman",
  years_experience: 4,
  resume_text:
    "Python, FastAPI, AWS, Docker, PostgreSQL, API optimization, monitoring, CI/CD",
});
addCandidate({
  name: "Riya",
  years_experience: 3,
  resume_text:
    "Django, Azure, Kubernetes, Terraform, SQL, backend service integrations, observability",
});
addCandidate({
  name: "Nikhil",
  years_experience: 5,
  resume_text:
    "Java Spring, microservices, AWS, Docker, Jenkins, PostgreSQL, incident response",
});

  updateModeVisibility();
  updateUploadPreview();

// =============================================================================
// Minimal SPA View Router
// =============================================================================

function switchMode(mode) {
  const recruiterView = document.getElementById("recruiter-view");
  const candidateView = document.getElementById("candidate-view");
  const navRecruiter = document.getElementById("nav-recruiter");
  const navCandidate = document.getElementById("nav-candidate");

  const isRecruiter = mode === "recruiter";

  recruiterView.classList.toggle("hidden", !isRecruiter);
  candidateView.classList.toggle("hidden", isRecruiter);

  navRecruiter.classList.toggle("active", isRecruiter);
  navRecruiter.setAttribute("aria-selected", isRecruiter ? "true" : "false");

  navCandidate.classList.toggle("active", !isRecruiter);
  navCandidate.setAttribute("aria-selected", !isRecruiter ? "true" : "false");

  window.location.hash = mode;
}

document.getElementById("nav-recruiter")?.addEventListener("click", () => switchMode("recruiter"));
document.getElementById("nav-candidate")?.addEventListener("click", () => switchMode("candidate"));

// Initial route check on page load
if (window.location.hash === "#candidate") {
  switchMode("candidate");
}

