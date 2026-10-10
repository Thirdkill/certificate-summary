/**
 * Certificate OCR System — Frontend Application Logic
 * Vanilla JS, no build step. Talks to the FastAPI backend over fetch().
 */

const API = {
  extract: (lang) => `/extract?lang=${encodeURIComponent(lang)}`,
  batch: (lang) => `/batch-extract?lang=${encodeURIComponent(lang)}`,
  languages: "/languages",
  documents: "/documents",
  result: (id) => `/results/${id}`,
  deleteDoc: (id) => `/documents/${id}`,
  qrcode: (id) => `/certificates/${id}/qrcode`,
  exportExcel: "/export/excel",
  auditLog: "/audit-log",
};

// ---------------------------------------------------------------------------
// Navigation between the three views (Scan / Registry / Audit Trail)
// ---------------------------------------------------------------------------
document.querySelectorAll(".navlink").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".navlink").forEach((b) => b.classList.remove("is-active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("is-active"));
    btn.classList.add("is-active");
    document.getElementById(`view-${btn.dataset.view}`).classList.add("is-active");
    if (btn.dataset.view === "registry") loadRegistry();
    if (btn.dataset.view === "audit") loadAuditLog();
  });
});

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("is-error", isError);
  toast.classList.add("is-visible");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

// ---------------------------------------------------------------------------
// Load supported languages into the <select>
// ---------------------------------------------------------------------------
async function loadLanguages() {
  const select = document.getElementById("lang-select");
  try {
    const res = await fetch(API.languages);
    const data = await res.json();
    select.innerHTML = "";
    Object.entries(data.supported_languages).forEach(([code, name]) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = `${name} (${code})`;
      select.appendChild(opt);
    });
  } catch (e) {
    select.innerHTML = '<option value="eng">English (eng)</option>';
  }
}
loadLanguages();

// ---------------------------------------------------------------------------
// Drag & drop / click-to-browse upload
// ---------------------------------------------------------------------------
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const batchToggle = document.getElementById("batch-toggle");
const scannerLabel = document.getElementById("scanner-label");

dropzone.addEventListener("click", () => fileInput.click());

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("is-dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length) handleFiles(files);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFiles(fileInput.files);
});

batchToggle.addEventListener("change", () => {
  fileInput.multiple = batchToggle.checked;
  scannerLabel.textContent = batchToggle.checked
    ? "Drag multiple certificates here, or click to browse"
    : "Drag a certificate here, or click to browse";
});

function handleFiles(fileList) {
  const lang = document.getElementById("lang-select").value || "eng";
  if (batchToggle.checked && fileList.length > 1) {
    runBatchExtract(fileList, lang);
  } else {
    runExtract(fileList[0], lang);
  }
}

function setBusy(isBusy, label) {
  dropzone.classList.toggle("is-busy", isBusy);
  scannerLabel.textContent = label || scannerLabel.textContent;
}

// ---------------------------------------------------------------------------
// Single-file extraction
// ---------------------------------------------------------------------------
async function runExtract(file, lang) {
  document.getElementById("results").hidden = true;
  document.getElementById("results-batch").hidden = true;
  setBusy(true, `Scanning ${file.name}…`);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(API.extract(lang), { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Extraction failed");
    renderResult(data);
    showToast(`Extracted "${file.name}" in ${data.processing_time_seconds}s`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    setBusy(false, "Drag a certificate here, or click to browse");
    fileInput.value = "";
  }
}

function renderResult(data) {
  const sheet = document.getElementById("results-sheet");
  const conf = data.ocr_confidence || 0;

  const rows = [
    ["Candidate Name", data.candidate_name],
    ["Certificate Title", data.certificate_title],
    ["Organization", data.organization_name],
    ["Issue Date", data.issue_date],
    ["Certificate Number", data.certificate_number],
    ["Grade / Score", data.grade_score],
    ["Duration", data.duration],
  ];

  sheet.innerHTML = `
    <div class="ledger-head">
      <div>
        <h3>${escapeHtml(data.candidate_name || "Unrecognized Candidate")}</h3>
        <span class="file-tag">${escapeHtml(data.filename)} · ID ${data.id.slice(0, 8)}</span>
      </div>
      <div class="confidence-badge">
        <span class="confidence-badge__label">OCR Confidence</span>
        <div class="confidence-bar"><div class="confidence-bar__fill" style="width:${conf}%"></div></div>
        <span class="confidence-badge__value">${conf}%</span>
      </div>
    </div>
    ${rows
      .map(
        ([label, value]) => `
      <div class="ledger-row">
        <span class="ledger-row__label">${label}</span>
        <span class="ledger-row__leader"></span>
        <span class="ledger-row__value ${value ? "" : "is-empty"}">${
          value ? escapeHtml(value) : "Not detected"
        }</span>
      </div>`
      )
      .join("")}
    <div class="ledger-actions">
      <button class="btn" id="qr-btn">Generate QR code</button>
      <button class="btn btn--ghost" id="copy-btn">Copy as JSON</button>
    </div>
    <details class="raw-text-toggle">
      <summary>View raw OCR text</summary>
      <pre>${escapeHtml(data.raw_text || "(no text detected)")}</pre>
    </details>
  `;

  document.getElementById("results").hidden = false;
  document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "nearest" });

  document.getElementById("qr-btn").addEventListener("click", () => {
    window.open(API.qrcode(data.id), "_blank");
  });
  document.getElementById("copy-btn").addEventListener("click", () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    showToast("Copied result JSON to clipboard");
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Batch extraction (Bonus Feature)
// ---------------------------------------------------------------------------
async function runBatchExtract(fileList, lang) {
  document.getElementById("results").hidden = true;
  setBusy(true, `Scanning ${fileList.length} certificates…`);

  const formData = new FormData();
  Array.from(fileList).forEach((f) => formData.append("files", f));

  try {
    const res = await fetch(API.batch(lang), { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Batch extraction failed");
    renderBatchResults(data.results);
    showToast(`Processed ${data.total} certificates`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    setBusy(false, "Drag multiple certificates here, or click to browse");
    fileInput.value = "";
  }
}

function renderBatchResults(results) {
  const tbody = document.getElementById("batch-table-body");
  tbody.innerHTML = results
    .map((r) => {
      const ok = r.status === "success";
      return `
      <tr>
        <td>${escapeHtml(r.filename)}</td>
        <td>${ok ? escapeHtml(r.candidate_name || "—") : "—"}</td>
        <td>${ok ? escapeHtml(r.certificate_title || "—") : "—"}</td>
        <td>${ok ? (r.ocr_confidence || 0) + "%" : "—"}</td>
        <td><span class="status-pill status-pill--${ok ? "success" : "failed"}">${
        ok ? "Success" : "Failed"
      }</span></td>
      </tr>`;
    })
    .join("");
  document.getElementById("results-batch").hidden = false;
}

// ---------------------------------------------------------------------------
// Registry view
// ---------------------------------------------------------------------------
async function loadRegistry() {
  const tbody = document.getElementById("registry-table-body");
  try {
    const res = await fetch(API.documents);
    const docs = await res.json();
    if (!docs.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No certificates processed yet.</td></tr>';
      return;
    }
    tbody.innerHTML = docs
      .map(
        (d) => `
      <tr>
        <td>${escapeHtml(d.candidate_name || "Unrecognized")}</td>
        <td>${escapeHtml(d.certificate_title || "—")}</td>
        <td>${new Date(d.created_at).toLocaleString()}</td>
        <td><button class="btn btn--ghost btn--small" data-delete="${d.id}">Delete</button></td>
      </tr>`
      )
      .join("");

    tbody.querySelectorAll("[data-delete]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetch(API.deleteDoc(btn.dataset.delete), { method: "DELETE" });
        showToast("Certificate deleted");
        loadRegistry();
      });
    });
  } catch (e) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="4">Could not load registry.</td></tr>';
  }
}

document.getElementById("export-excel-btn").addEventListener("click", () => {
  window.open(API.exportExcel, "_blank");
});

// ---------------------------------------------------------------------------
// Audit trail view (Bonus Feature)
// ---------------------------------------------------------------------------
async function loadAuditLog() {
  const tbody = document.getElementById("audit-table-body");
  try {
    const res = await fetch(API.auditLog);
    const logs = await res.json();
    if (!logs.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No activity yet.</td></tr>';
      return;
    }
    tbody.innerHTML = logs
      .map(
        (l) => `
      <tr>
        <td>${new Date(l.timestamp).toLocaleString()}</td>
        <td>${escapeHtml(l.filename)}</td>
        <td>${escapeHtml(l.action)}</td>
        <td><span class="status-pill status-pill--${l.status === "SUCCESS" ? "success" : "failed"}">${l.status}</span></td>
        <td>${escapeHtml(l.details || "—")}</td>
      </tr>`
      )
      .join("");
  } catch (e) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">Could not load audit log.</td></tr>';
  }
}
