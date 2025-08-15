const threatContainer = document.getElementById("threat-container");
const searchInput = document.getElementById("search-input");
const sourceFilter = document.getElementById("source-filter");
const typeFilter = document.getElementById("type-filter");
const readFilter = document.getElementById("read-filter");
const cacheIntervalSelect = document.getElementById("cache-interval");
const refreshNowBtn = document.getElementById("refresh-now");
const darkModeToggle = document.getElementById("dark-mode-toggle");

const contentGrid = document.getElementById("contentGrid");
const panel = document.getElementById("detail-panel");
const panelTitle = document.getElementById("panel-title");
const panelBody = document.getElementById("panel-body");
const panelLink = document.getElementById("panel-link");
const panelClose = document.getElementById("panel-close");
const toastEl = document.getElementById("toast");

let threats = [];

// --- helpers ---
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2200);
}

function snippet(text, n = 220) {
  if (!text) return "";
  const t = text.trim();
  return t.length > n ? t.slice(0, n) + "…" : t;
}

function applyDarkFromStorage() {
  const saved = localStorage.getItem("dark-mode") === "1";
  document.body.classList.toggle("dark-mode", saved);
  darkModeToggle.textContent = saved ? "☀️" : "🌙";
}

// --- data fetch ---
async function fetchThreats() {
  const res = await fetch("/api/threats");
  threats = await res.json();
  populateFilters();
  renderThreats();
}

function populateFilters() {
  const sources = Array.from(new Set(threats.map(t => t.source || "Unknown"))).sort();
  const types = Array.from(new Set(threats.map(t => t.type || "Unknown"))).sort();

  sourceFilter.innerHTML = `<option value="">All Sources</option>` + sources.map(s => `<option value="${s}">${s}</option>`).join("");
  typeFilter.innerHTML = `<option value="">All Types</option>` + types.map(t => `<option value="${t}">${t}</option>`).join("");
  readFilter.innerHTML = `<option value="">All</option><option value="read">Read</option><option value="unread">Unread</option>`;
}

function renderThreats() {
  const searchText = (searchInput.value || "").toLowerCase();
  const sVal = sourceFilter.value;
  const tVal = typeFilter.value;
  const rVal = readFilter.value;

  threatContainer.innerHTML = "";

  threats
    .filter(t =>
      (!sVal || t.source === sVal) &&
      (!tVal || t.type === tVal) &&
      (!rVal || (rVal === "read" ? t.read_flag : !t.read_flag)) &&
      ((t.title || "").toLowerCase().includes(searchText) || (t.description || "").toLowerCase().includes(searchText))
    )
    .forEach(t => {
      const col = document.createElement("div");
      col.className = "col-12 col-md-6 col-xl-4";

      const card = document.createElement("div");
      card.className = `card ${t.read_flag ? "read" : "unread"} p-3 h-100`;
      card.innerHTML = `
        <h5 class="mb-2">${t.title || ""}</h5>
        <p class="mb-1">${snippet(t.description)}</p>
        <div class="mt-2 d-flex align-items-center gap-1 flex-wrap">
          <span class="badge bg-info text-dark">${t.source || "Unknown"}</span>
          <span class="badge bg-warning text-dark">${t.type || "Unknown"}</span>
        </div>
      `;
      card.addEventListener("click", () => openPanel(t));
      col.appendChild(card);
      threatContainer.appendChild(col);
    });
}

function openPanel(threat) {
  panelTitle.textContent = threat.title || "";
  panelBody.textContent = threat.description || "";
  panelLink.href = threat.link || "#";

  // Slide in panel (grid column expands)
  contentGrid.classList.add("with-panel");

  // Mark read
  if (!threat.read_flag) {
    fetch(`/api/mark_read/${encodeURIComponent(threat.id)}`, { method: "POST" })
      .then(() => {
        threat.read_flag = 1;
        renderThreats();
      })
      .catch(() => {});
  }
}

function closePanel() {
  contentGrid.classList.remove("with-panel");
}

// --- events ---
panelClose.addEventListener("click", closePanel);

searchInput.addEventListener("input", renderThreats);
sourceFilter.addEventListener("change", renderThreats);
typeFilter.addEventListener("change", renderThreats);
readFilter.addEventListener("change", renderThreats);

cacheIntervalSelect.addEventListener("change", async () => {
  const minutes = parseInt(cacheIntervalSelect.value, 10);
  try {
    const res = await fetch("/api/set_cache_interval", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ minutes })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || "Interval updated.");
      await fetchThreats();
    } else {
      showToast(data.message || "Failed to update interval.");
    }
  } catch {
    showToast("Failed to update interval.");
  }
});

refreshNowBtn.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || "Feeds refreshed.");
      await fetchThreats();
    } else {
      showToast(data.message || "Refresh failed.");
    }
  } catch {
    showToast("Refresh failed.");
  }
});

darkModeToggle.addEventListener("click", () => {
  const willEnable = !document.body.classList.contains("dark-mode");
  document.body.classList.toggle("dark-mode", willEnable);
  localStorage.setItem("dark-mode", willEnable ? "1" : "0");
  darkModeToggle.textContent = willEnable ? "☀️" : "🌙";
});

// --- boot ---
applyDarkFromStorage();
fetchThreats();
