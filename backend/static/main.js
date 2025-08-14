const threatContainer = document.getElementById("threat-container");
const searchInput = document.getElementById("search-input");
const sourceFilter = document.getElementById("source-filter");
const typeFilter = document.getElementById("type-filter");
const readFilter = document.getElementById("read-filter");
const darkModeToggle = document.getElementById("dark-mode-toggle");

let threats = [];

// Fetch threats from backend
async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    populateFilters();
    renderThreats();
}

// Render filters dynamically
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

// Render threats
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
            card.className = `card ${t.read_flag ? "read" : "unread"} mb-2 p-2`;
            card.innerHTML = `
                <h5>${t.title}</h5>
                <p>${t.description.slice(0, 200)}${t.description.length > 200 ? "..." : ""}</p>
                <div>
                    <span class="badge bg-info">${t.source}</span>
                    <span class="badge bg-warning text-dark">${t.type}</span>
                </div>
            `;

            // Click to open modal
            card.addEventListener("click", () => showModal(t));

            threatContainer.appendChild(card);
        });
}

// Show modal with full description
function showModal(threat) {
    const modalTitle = document.getElementById("modal-title");
    const modalBody = document.getElementById("modal-body");
    const modalLink = document.getElementById("modal-link");

    modalTitle.textContent = threat.title;
    modalBody.textContent = threat.description;
    modalLink.href = threat.link;

    // Mark as read instantly
    if (!threat.read_flag) {
        fetch(`/api/mark_read/${threat.id}`, { method: "POST" })
            .then(() => {
                threat.read_flag = 1;
                renderThreats();
            });
    }

    new bootstrap.Modal(document.getElementById("threatModal")).show();
}

// Event listeners
searchInput.addEventListener("input", renderThreats);
sourceFilter.addEventListener("change", renderThreats);
typeFilter.addEventListener("change", renderThreats);
readFilter.addEventListener("change", renderThreats);

darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

// Initial fetch
fetchThreats();
