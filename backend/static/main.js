const threatContainer = document.getElementById("threat-container");
const searchInput = document.getElementById("search-input");
const sourceFilter = document.getElementById("source-filter");
const typeFilter = document.getElementById("type-filter");
const readFilter = document.getElementById("read-filter");
const cacheIntervalSelect = document.getElementById("cache-interval");
const darkModeToggle = document.getElementById("dark-mode-toggle");

let threats = [];

// Fetch threats from backend
async function fetchThreats() {
    try {
        const res = await fetch("/api/threats");
        threats = await res.json();
        populateFilters();
        renderThreats();
    } catch (err) {
        console.error("Error fetching threats:", err);
    }
}

// Populate filter dropdowns
function populateFilters() {
    const sources = new Set(threats.map(t => t.source || "Unknown"));
    const types = new Set(threats.map(t => t.type || "Unknown"));

    sourceFilter.innerHTML = `<option value="">All Sources</option>` +
        [...sources].map(s => `<option value="${s}">${s}</option>`).join("");

    typeFilter.innerHTML = `<option value="">All Types</option>` +
        [...types].map(t => `<option value="${t}">${t}</option>`).join("");

    readFilter.innerHTML = `
        <option value="">All</option>
        <option value="read">Read</option>
        <option value="unread">Unread</option>
    `;
}

// Render threat cards
function renderThreats() {
    const searchText = searchInput.value.toLowerCase();
    const sourceVal = sourceFilter.value;
    const typeVal = typeFilter.value;
    const readVal = readFilter.value;

    threatContainer.innerHTML = "";

    threats
        .filter(t =>
            (!sourceVal || t.source === sourceVal) &&
            (!typeVal || t.type === typeVal) &&
            (!readVal || (readVal === "read" ? t.read_flag : !t.read_flag)) &&
            (t.title.toLowerCase().includes(searchText) || t.description.toLowerCase().includes(searchText))
        )
        .forEach(t => {
            const card = document.createElement("div");
            card.className = `card ${t.read_flag ? "read" : "unread"} p-3`;
            card.innerHTML = `
                <h5>${t.title}</h5>
                <p>${t.description.length > 200 ? t.description.slice(0, 200) + "..." : t.description}</p>
                <div>
                    <span class="badge bg-info">${t.source}</span>
                    <span class="badge bg-warning text-dark">${t.type}</span>
                </div>
            `;
            card.addEventListener("click", () => showModal(t));
            threatContainer.appendChild(card);
        });
}

// Show modal with full threat details
function showModal(threat) {
    document.getElementById("modal-title").textContent = threat.title;
    document.getElementById("modal-body").textContent = threat.description;
    document.getElementById("modal-link").href = threat.link || "#";

    if (!threat.read_flag) {
        fetch(`/api/mark_read/${threat.id}`, { method: "POST" })
            .then(() => {
                threat.read_flag = 1;
                renderThreats();
            });
    }

    new bootstrap.Modal(document.getElementById("threatModal")).show();
}

// Set cache interval
cacheIntervalSelect.addEventListener("change", () => {
    const minutes = parseInt(cacheIntervalSelect.value, 10);
    fetch("/api/set_cache_interval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ minutes })
    }).then(res => {
        if (!res.ok) console.error("Failed to set cache interval");
    });
});

// Event listeners
searchInput.addEventListener("input", renderThreats);
sourceFilter.addEventListener("change", renderThreats);
typeFilter.addEventListener("change", renderThreats);
readFilter.addEventListener("change", renderThreats);
darkModeToggle.addEventListener("click", () => document.body.classList.toggle("dark-mode"));

// Initial load
fetchThreats();
