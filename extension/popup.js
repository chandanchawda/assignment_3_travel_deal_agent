// ============================================================
// Travel Deal Investigator — Chrome Extension (Frontend)
// Thin client: sends deal text to Python FastAPI backend,
// receives reasoning chain + verdict, and renders it.
// ============================================================

const BACKEND_URL = "http://localhost:5000";

// ---- DOM Elements ----
const apiKeyInput = document.getElementById("apiKeyInput");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const backendStatus = document.getElementById("backendStatus");
const statusDot = backendStatus.querySelector(".status-dot");
const statusText = backendStatus.querySelector(".status-text");
const dealInput = document.getElementById("dealInput");
const investigateBtn = document.getElementById("investigateBtn");
const reasoningChain = document.getElementById("reasoningChain");
const chainSteps = document.getElementById("chainSteps");
const stepCounter = document.getElementById("stepCounter");
const finalVerdict = document.getElementById("finalVerdict");
const logsSection = document.getElementById("logsSection");
const toggleLogs = document.getElementById("toggleLogs");
const logActions = document.getElementById("logActions");
const copyLogsBtn = document.getElementById("copyLogsBtn");
const logOutput = document.getElementById("logOutput");
const modeBtns = document.querySelectorAll(".mode-btn");

let API_KEY = "";
let backendOnline = false;

// ============================================================
// 1. BACKEND HEALTH CHECK
// ============================================================

async function checkBackend() {
  statusDot.className = "status-dot checking";
  statusText.textContent = "Checking backend...";

  try {
    const res = await fetch(`${BACKEND_URL}/health`, { method: "GET" });
    if (res.ok) {
      backendOnline = true;
      statusDot.className = "status-dot online";
      statusText.textContent = "Python backend connected (localhost:5000)";
    } else {
      throw new Error("Not OK");
    }
  } catch {
    backendOnline = false;
    statusDot.className = "status-dot offline";
    statusText.textContent = "Backend offline — run: python server.py";
  }

  updateInvestigateBtn();
}

// Check on load
checkBackend();
// Re-check every 10 seconds
setInterval(checkBackend, 10000);

// ============================================================
// 2. API KEY MANAGEMENT
// ============================================================

saveKeyBtn.addEventListener("click", () => {
  API_KEY = apiKeyInput.value.trim();
  if (API_KEY) {
    chrome.storage.local.set({ geminiKey: API_KEY });
    saveKeyBtn.textContent = "Saved ✓";
    setTimeout(() => { saveKeyBtn.textContent = "Save"; }, 1500);
    updateInvestigateBtn();
  }
});

chrome.storage.local.get("geminiKey", (data) => {
  if (data.geminiKey) {
    API_KEY = data.geminiKey;
    apiKeyInput.value = data.geminiKey;
    updateInvestigateBtn();
  }
});

// ============================================================
// 3. MODE BUTTONS (Scan Page / Manual)
// ============================================================

modeBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    modeBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    if (btn.dataset.mode === "page") {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: "extractPageContent" }, (response) => {
          if (response && response.text) {
            dealInput.value = `[From: ${response.title}]\n${response.url}\n\n${response.text.substring(0, 2000)}`;
          } else {
            dealInput.placeholder = "Could not extract page content. Try Manual Input.";
          }
          updateInvestigateBtn();
        });
      });
    } else {
      dealInput.value = "";
      dealInput.placeholder = "Paste a travel deal here... e.g., 'Round trip flights from NYC to Tokyo for $450 in December 2025 on Delta Airlines'";
      updateInvestigateBtn();
    }
  });
});

// ============================================================
// 4. INVESTIGATE — CALL PYTHON BACKEND
// ============================================================

investigateBtn.addEventListener("click", async () => {
  const dealText = dealInput.value.trim();
  if (!dealText || !API_KEY || !backendOnline) return;

  resetUI();
  reasoningChain.classList.remove("hidden");
  logsSection.classList.remove("hidden");

  investigateBtn.innerHTML = '<div class="spinner"></div> Agent is investigating...';
  investigateBtn.classList.add("loading");

  try {
    const res = await fetch(`${BACKEND_URL}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        deal_text: dealText,
        api_key: API_KEY
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `Server error: ${res.status}`);
    }

    const data = await res.json();

    // Render reasoning chain steps
    data.steps.forEach((step, i) => {
      addStepCard(step.type, step.title, step.content);
    });

    stepCounter.textContent = `${data.iterations} iterations`;

    // Render final verdict
    showVerdict(data.final_answer);

    // Store logs
    logOutput.textContent = data.logs;

  } catch (err) {
    addStepCard("error", "Error", err.message);
  }

  investigateBtn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
    Investigate This Deal
  `;
  investigateBtn.classList.remove("loading");
});

// ============================================================
// 5. UI HELPER FUNCTIONS
// ============================================================

function addStepCard(type, title, content) {
  const card = document.createElement("div");
  card.className = "step-card";

  // Format content: if it looks like JSON, wrap in <pre>
  let displayContent = content;
  try {
    const parsed = JSON.parse(content);
    displayContent = `<pre>${JSON.stringify(parsed, null, 2)}</pre>`;
  } catch {
    // Not JSON — render as formatted text
    displayContent = formatText(content);
  }

  card.innerHTML = `
    <div class="step-label ${type}">
      <span class="step-dot"></span>
      ${title}
    </div>
    <div class="step-content">${displayContent}</div>
  `;
  chainSteps.appendChild(card);
  card.scrollIntoView({ behavior: "smooth", block: "end" });
}

function showVerdict(text) {
  const lower = text.toLowerCase();
  let score = "good";
  if (lower.includes("great deal") || lower.includes("excellent deal")) score = "great";
  else if (lower.includes("bad deal") || lower.includes("overpriced") || lower.includes("avoid")) score = "bad";

  const badgeLabel = score === "great" ? "Great Deal" : score === "bad" ? "Bad Deal" : "Good Deal";

  finalVerdict.innerHTML = `
    <div class="verdict-header">
      <span class="verdict-badge ${score}">${badgeLabel}</span>
      <span class="verdict-title">Final Verdict</span>
    </div>
    <div class="verdict-body">${formatText(text)}</div>
  `;
  finalVerdict.classList.remove("hidden");
  finalVerdict.scrollIntoView({ behavior: "smooth" });
}

function formatText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>")
    .replace(/#{1,3}\s?(.*?)(<br>|$)/g, "<strong>$1</strong><br>");
}

function resetUI() {
  chainSteps.innerHTML = "";
  finalVerdict.innerHTML = "";
  finalVerdict.classList.add("hidden");
  reasoningChain.classList.add("hidden");
  logsSection.classList.add("hidden");
  logOutput.classList.add("hidden");
  logActions.classList.add("hidden");
  stepCounter.textContent = "Step 0";
  logOutput.textContent = "";
}

function updateInvestigateBtn() {
  investigateBtn.disabled = !dealInput.value.trim() || !API_KEY || !backendOnline;
}

// ============================================================
// 6. LOGS TOGGLE + COPY
// ============================================================

toggleLogs.addEventListener("click", () => {
  const isHidden = logOutput.classList.toggle("hidden");
  logActions.classList.toggle("hidden", isHidden);
  toggleLogs.querySelector("svg + *") || null;
});

copyLogsBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(logOutput.textContent).then(() => {
    copyLogsBtn.textContent = "✓ Copied!";
    setTimeout(() => { copyLogsBtn.textContent = "📋 Copy Logs"; }, 1500);
  });
});

// Update button state on input
dealInput.addEventListener("input", updateInvestigateBtn);
