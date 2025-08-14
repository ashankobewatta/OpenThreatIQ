let threats = [];
let darkMode = false;

const searchBar = document.getElementById("search-bar");
const filterSource = document.getElementById("filter-source");
const filterType = document.getElementById("filter-type");
const filterRead = document.getElementById("filter-read");
const container = document.getElementById("threat-container");
const modalDescription = document.getElementById("modal-description");
const threatModal = new bootstrap.Modal(document.getElementById('threatModal'));

async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    populateFilters();
    renderThreats();
}

function populateFilters() {
    const sources = new Set(["All"]);
    const types = new Set(["All"]);
    threats.forEach(t => {
        sources.add(t.source || "Unknown");
        types.add(t.type || "Unknown");
    });

    filterSource.innerHTML = Array.from(sources).map(s => `<option value="${s}">${s}</option>`).join("");
    filterType.innerHTML = Array.from(types).map(t => `<option value="${t}">${t}</option>`).join("");
}

function renderThreats() {
    const searchText = searchBar.value.toLowerCase();
    const selectedSource = filterSource.value;
    const selectedType = filterType.value;
    const selectedRead = filterRead.value;

    container.innerHTML = "";

    threats.forEach(t => {
        if (selectedSource !== "All" && t.source !== selectedSource) return;
        if (selectedType !== "All" && t.type !== selectedType) return;
        if (selectedRead === "Read" && t.read_flag !== 1) return;
        if (selectedRead === "Unread" && t.read_flag !== 0) return;
        if (searchText && !(t.title.toLowerCase().includes(searchText) || t.description.toLowerCase().includes(searchText))) return;

        const card = document.createElement("div");
        card.className = "col-md-4";
        card.innerHTML = `
            <div class="card threat-card ${t.read_flag ? 'read' : 'unread'}">
                <div class="card-body">
                    <h5 class="card-title">${t.title}</h5>
                    <span class="badge bg-primary">${t.type || "Unknown"}</span>
                    <span class="badge bg-secondary">${t.source || "Unknown"}</span>
                    <p class="card-text">${t.description.substring(0, 100)}...</p>
                    <button class="btn btn-sm btn-outline-primary btn-view">View</button>
                    <button class="btn btn-sm btn-outline-success btn-read">${t.read_flag ? 'Mark Unread' : 'Mark Read'}</button>
                </div>
            </div>
        `;
        container.appendChild(card);

        card.querySelector(".btn-view").addEventListener("click", () => {
            modalDescription.innerHTML = t.description;
            threatModal.show();
        });

        card.querySelector(".btn-read").addEventListener("click", async () => {
            await fetch("/api/mark_read", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({id: t.id})
            });
            t.read_flag = t.read_flag ? 0 : 1;
            renderThreats();
        });
    });
}

searchBar.addEventListener("input", renderThreats);
filterSource.addEventListener("change", renderThreats);
filterType.addEventListener("change", renderThreats);
filterRead.addEventListener("change", renderThreats);

document.getElementById("dark-toggle").addEventListener("click", () => {
    darkMode = !darkMode;
    document.body.classList.toggle("dark-mode", darkMode);
});

fetchThreats();
