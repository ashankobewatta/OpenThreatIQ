const threatContainer = document.getElementById("threat-container");
const searchInput = document.getElementById("search-input");
const sourceFilter = document.getElementById("source-filter");
const typeFilter = document.getElementById("type-filter");
const readFilter = document.getElementById("read-filter");
const cacheIntervalSelect = document.getElementById("cache-interval");
const darkModeToggle = document.getElementById("dark-mode-toggle");

const popupPanel = document.getElementById("popup-panel");
const popupTitle = document.getElementById("popup-title");
const popupBody = document.getElementById("popup-body");
const popupLink = document.getElementById("popup-link");
const popupClose = document.getElementById("popup-close");

let threats = [];

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
                <p>${t.description.slice(0, 200)}...</p>
                <div>
                    <span class="badge bg-info">${t.source}</span>
                    <span class="badge bg-warning text-dark">${t.type}</span>
                </div>
            `;
            card.addEventListener("click", () => showPopup(t));
            threatContainer.appendChild(card);
        });
}

function showPopup(threat) {
    popupTitle.textContent = threat.title;
    popupBody.textContent = threat.description; // full content
    popupLink.href = threat.link || "#";

    document.querySelector(".main-content").classList.add("popup-open");
    popupPanel.classList.add("open");

    if (!threat.read_flag) {
        fetch(`/api/mark_read/${encodeURIComponent(threat.id)}`, { method: "POST" })
            .then(() => {
                threat.read_flag = 1;
                renderThreats();
            });
    }
}

function closePopup() {
    popupPanel.classList.remove("open");
    document.querySelector(".main-content").classList.remove("popup-open");
}

// Event listeners
popupClose.addEventListener("click", closePopup);
searchInput.addEventListener("input", renderThreats);
sourceFilter.addEventListener("change", renderThreats);
typeFilter.addEventListener("change", renderThreats);
readFilter.addEventListener("change", renderThreats);

cacheIntervalSelect.addEventListener("change", () => {
    const minutes = parseInt(cacheIntervalSelect.value, 10);
    fetch("/api/set_cache_interval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ minutes })
    }).then(res => {
        if (!res.ok) console.error("Failed to set cache interval");
        else fetchThreats(); // immediately refresh threats
    });
});

darkModeToggle.addEventListener("click", () => document.body.classList.toggle("dark-mode"));

// Initial load
fetchThreats();
