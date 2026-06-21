/* MediSight AI frontend + backend integration (no SPA) */

const API = {
  uploadImage: "/upload-image",
  submitVitals: "/submit-vitals",
  submitSymptoms: "/submit-symptoms",
  analyzeCase: "/analyze-case",
  result: (id) => `/result/${id}`,
  history: "/history",
};

function getCaseId() {
  return localStorage.getItem("medisight_case_id");
}

function setCaseId(caseId) {
  localStorage.setItem("medisight_case_id", String(caseId));
}

function showAlert(msg) {
  window.alert(msg);
}

function highlightActiveNav() {
  const file = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-link[data-page]").forEach((link) => {
    if (link.dataset.page === file) link.classList.add("active");
  });
}

function initUploadPage() {
  const uploadZone = document.getElementById("uploadZone");
  const fileInput = document.getElementById("imageFile");
  const previewBox = document.getElementById("previewBox");
  const qualityMsg = document.getElementById("qualityMsg");
  const nextBtn = document.getElementById("uploadNextBtn");
  const imageTypeEl = document.getElementById("imageType");

  if (!uploadZone || !fileInput || !previewBox || !qualityMsg || !nextBtn || !imageTypeEl) return;

  let selectedFile = null;

  const renderPreview = (file) => {
    if (!file || !file.type.startsWith("image/")) {
      qualityMsg.textContent = "Please upload a valid image file.";
      qualityMsg.className = "text-danger";
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewBox.innerHTML = `<img src="${e.target.result}" alt="Uploaded preview" />`;
      qualityMsg.textContent = "Image selected. Ready to upload.";
      qualityMsg.className = "text-secondary";
    };
    reader.readAsDataURL(file);
  };

  uploadZone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => renderPreview(fileInput.files[0]));

  ["dragenter", "dragover"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.remove("dragover");
    });
  });

  uploadZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    fileInput.files = e.dataTransfer.files;
    renderPreview(file);
  });

  nextBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      showAlert("Please select an image first.");
      return;
    }

    const form = new FormData();
    form.append("image", selectedFile);
    form.append("image_type", imageTypeEl.value);
    const caseId = getCaseId();
    if (caseId) form.append("case_id", caseId);

    nextBtn.disabled = true;
    nextBtn.textContent = "Uploading...";

    try {
      const res = await fetch(API.uploadImage, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Upload failed");
      setCaseId(data.case_id);
      qualityMsg.textContent = data.image_quality || "Image uploaded.";
      qualityMsg.className = data.quality_flag === "poor" ? "text-danger" : "text-success";
      window.location.href = "vitals.html";
    } catch (err) {
      showAlert(err.message);
    } finally {
      nextBtn.disabled = false;
      nextBtn.textContent = "Next: Enter Vitals";
    }
  });
}

function initVitalsPage() {
  const form = document.getElementById("vitalsForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.checkValidity()) {
      form.classList.add("was-validated");
      return;
    }

    const vitals = {
      age: document.getElementById("age").value,
      sex: document.getElementById("sex").value,
      sbp: document.getElementById("sbp").value,
      dbp: document.getElementById("dbp").value,
      heart_rate: document.getElementById("heartRate").value,
      temperature: document.getElementById("temperature").value,
      respiratory_rate: document.getElementById("respiratoryRate").value,
      spo2: document.getElementById("spo2").value,
      weight: document.getElementById("weight").value,
      glucose: document.getElementById("glucose").value,
    };

    try {
      const res = await fetch(API.submitVitals, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: Number(getCaseId()), vitals }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Vitals submission failed");
      setCaseId(data.case_id);
      window.location.href = "symptoms.html";
    } catch (err) {
      showAlert(err.message);
    }
  });
}

function initSymptomsPage() {
  const form = document.getElementById("symptomsForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = document.getElementById("symptomsText");
    const duration = document.getElementById("duration").value;
    const severity = document.getElementById("severity").value;

    if (!text.value.trim()) {
      text.classList.add("is-invalid");
      return;
    }
    text.classList.remove("is-invalid");

    const fullText = `${text.value.trim()} ${duration ? ` Duration: ${duration}.` : ""} ${severity ? ` Severity: ${severity}.` : ""}`.trim();

    try {
      const caseId = Number(getCaseId());
      const submitRes = await fetch(API.submitSymptoms, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, symptoms_text: fullText }),
      });
      const submitData = await submitRes.json();
      if (!submitRes.ok) throw new Error(submitData.error || "Symptoms submission failed");

      const analyzeRes = await fetch(API.analyzeCase, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });
      const analyzeData = await analyzeRes.json();
      if (!analyzeRes.ok) throw new Error(analyzeData.error || "Analysis failed");

      window.location.href = "result.html";
    } catch (err) {
      showAlert(err.message);
    }
  });
}

function initResultPage() {
  const container = document.getElementById("conditionsContainer");
  if (!container) return;

  const writeList = (id, values) => {
    const el = document.getElementById(id);
    if (!el) return;
    const list = values || [];
    el.innerHTML = list.length ? list.map((v) => `<li>${v}</li>`).join("") : "<li>None significant</li>";
  };

  const writeDashList = (id, values) => {
    const el = document.getElementById(id);
    if (!el) return;
    const list = values || [];
    el.innerHTML = list.length ? list.map((v) => `<li>${v}</li>`).join("") : "<li>None significant</li>";
  };

  const writeTagList = (id, values) => {
    const el = document.getElementById(id);
    if (!el) return;
    const list = values || [];
    el.innerHTML = list.length ? list.map((v) => `<span>${v}</span>`).join("") : "<span>None significant</span>";
  };

  const writeVitalsAssessment = (values) => {
    const el = document.getElementById("vitalsAssessmentList");
    if (!el) return;
    const list = values || [];
    if (!list.length) {
      el.innerHTML = `<div class="small text-secondary">No vitals assessment available.</div>`;
      return;
    }
    el.innerHTML = list.map((item) => {
      const status = item.status || "normal";
      const cls = status === "critical" ? "vital-critical" : status === "abnormal" ? "vital-abnormal" : "vital-normal";
      const arrow = item.direction === "up" ? "↑" : item.direction === "down" ? "↓" : "•";
      return `
        <div class="vital-row ${cls}">
          <span>${item.label}</span>
          <strong>${item.value} ${arrow}</strong>
        </div>
      `;
    }).join("");
  };

  const renderPrimaryVital = (values) => {
    const valueEl = document.getElementById("primaryVitalValue");
    const labelEl = document.getElementById("primaryVitalLabel");
    if (!valueEl || !labelEl) return;

    const list = values || [];
    const primary = list.find((item) => item.status === "critical")
      || list.find((item) => item.status === "abnormal")
      || list[0];
    if (!primary) {
      valueEl.textContent = "-";
      labelEl.textContent = "No abnormal vital";
      return;
    }
    const arrow = primary.direction === "up" ? "↑" : primary.direction === "down" ? "↓" : "";
    valueEl.innerHTML = `${primary.value} <span>${arrow}</span>`;
    labelEl.textContent = primary.label;
  };

  const load = async () => {
    const caseId = getCaseId();
    if (!caseId) {
      showAlert("No case found. Start from upload page.");
      return;
    }

    try {
      const res = await fetch(API.result(caseId));
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not load result");

      container.innerHTML = (data.possible_conditions || []).slice(0, 5).map((c) => {
        const score = Number(c.score || 0);
        const band = score >= 0.75 ? "High" : score >= 0.45 ? "Moderate" : "Low";
        const cls = band === "High" ? "pill-high" : band === "Moderate" ? "pill-moderate" : "pill-low";
        const components = c.components || {};
        return `
          <div class="condition-row">
            <div>
              <strong>${c.condition}</strong>
              <p>
                Image ${Math.round(Number(components.image || 0) * 100)}% ·
                Symptoms ${Math.round(Number(components.symptoms || 0) * 100)}% ·
                Vitals ${Math.round(Number(components.vitals || 0) * 100)}%
              </p>
            </div>
            <span class="result-pill ${cls}">${Math.round(score * 100)}%</span>
          </div>
        `;
      }).join("");

      writeList("evidenceList", data.evidence || []);
      writeList("abnormalVitalsList", data.abnormal_vitals || []);
      writeList("symptomsExtractedList", data.extracted_symptoms || []);
      writeTagList("riskFactorsList", data.risk_factors || []);
      writeList("emergencyFlagsList", data.emergency_flags || []);
      writeVitalsAssessment(data.vitals_assessment || []);
      renderPrimaryVital(data.vitals_assessment || []);

      const gemini = data.gemini || {};
      writeDashList("geminiWhyList", gemini.why_suggested || []);
      writeDashList("geminiRecommendationsList", gemini.recommendations || []);
      writeDashList("geminiQuestionsList", gemini.follow_up_questions || []);
      writeList("geminiLimitationsList", gemini.limitations || []);

      const urgency = document.getElementById("urgencyText");
      const urgentHeadline = document.getElementById("urgentHeadline");
      const urgentDetail = document.getElementById("urgentDetail");
      const urgentBanner = document.getElementById("urgentBanner");
      const recommendation = document.getElementById("recommendationText");
      const explanation = document.getElementById("explanationText");
      const disclaimer = document.getElementById("disclaimerText");
      const likelihoodBand = document.getElementById("likelihoodBand");
      const modelStatus = document.getElementById("modelStatus");
      const detectedModality = document.getElementById("detectedModality");
      const riskPercent = document.getElementById("riskPercent");
      const geminiStatus = document.getElementById("geminiStatus");

      const urgencyLabel = String(data.urgency || "moderate");
      const primaryAbnormal = (data.abnormal_vitals || [])[0] || "Review generated findings with a licensed clinician.";
      if (urgentBanner) urgentBanner.classList.toggle("is-low", urgencyLabel.toLowerCase() === "low");
      if (urgentHeadline) urgentHeadline.textContent = `${urgencyLabel.charAt(0).toUpperCase() + urgencyLabel.slice(1)} - clinician review required`;
      if (urgentDetail) urgentDetail.textContent = primaryAbnormal;
      if (urgency) urgency.textContent = `${urgencyLabel.toUpperCase()} - requires clinician review.`;
      if (recommendation) recommendation.textContent = gemini.summary || "Possible conditions include the ranked list above. Correlate with examination, labs, and clinician judgment before any treatment decision.";
      if (explanation) explanation.textContent = data.explanation || "No explanation available.";
      if (disclaimer) {
        disclaimer.textContent = `This is a prototype clinical decision support summary. It does not provide a confirmed diagnosis, prescribe medication, or invent missing patient details. Probability rankings require clinician review. Model status: ${data.model_status || "fallback baseline"}.`;
      }
      if (likelihoodBand) likelihoodBand.textContent = (data.likelihood_band || "low").toUpperCase();
      if (modelStatus) modelStatus.textContent = data.model_status || "fallback baseline";
      if (detectedModality) {
        const modality = (data.detected_modality || "general").replace("_", " ");
        detectedModality.textContent = modality.replace(/\b\w/g, (m) => m.toUpperCase());
      }
      if (riskPercent) riskPercent.innerHTML = `${Number(data.risk_percent || 0)}<span>/100</span>`;
      if (geminiStatus) {
        const status = data.reasoning_status === "gemini" ? "active" : "fallback";
        geminiStatus.textContent = `${gemini.model || "Gemini"} · ${status}`;
      }
    } catch (err) {
      showAlert(err.message);
    }
  };

  load();
}

function initHistoryPage() {
  const tbody = document.getElementById("historyTableBody");
  if (!tbody) return;

  const load = async () => {
    try {
      const res = await fetch(API.history);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load history");
      const items = data.items || [];
      if (!items.length) return;

      tbody.innerHTML = items.map((row) => {
        const urgency = String(row.urgency || "pending").toLowerCase();
        const cls = urgency === "urgent" ? "pill-high" : urgency === "moderate" ? "pill-moderate" : "pill-low";
        return `
          <tr>
            <td>${row.date}</td>
            <td>${row.case_id}</td>
            <td>${row.image_type}</td>
            <td><span class="result-pill ${cls} text-capitalize">${row.urgency}</span></td>
            <td><button class="btn btn-sm btn-outline-medical" data-view-id="${row.id}">View Report</button></td>
          </tr>
        `;
      }).join("");

      tbody.querySelectorAll("button[data-view-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          setCaseId(btn.dataset.viewId);
          window.location.href = "result.html";
        });
      });
    } catch (err) {
      showAlert(err.message);
    }
  };

  load();
}

document.addEventListener("DOMContentLoaded", () => {
  highlightActiveNav();
  initUploadPage();
  initVitalsPage();
  initSymptomsPage();
  initResultPage();
  initHistoryPage();
});
