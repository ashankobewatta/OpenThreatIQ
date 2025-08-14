let allCVEs = [];

// ------------------ Load cached data ------------------
async function loadCachedCVEs() {
    try {
        const response = await fetch("/api/cves"); // Reads backend cache
        allCVEs = await response.json();
    } catch (e) {
        console.error("Error fetching cache, using empty list.", e);
        allCVEs = [];
    }
    populateFilters();
    renderCVEs(allCVEs);
}

// ------------------ Populate dropdowns ------------------
function populateFilters() {
    const sourceSelect = document.getElementById("filter-source");
    const typeSelect = document.getElementById("filter-type");

    const sources = Array.from(new Set(allCVEs.map(c => c.source || "Unknown"))).sort();
    const types = Array.from(new Set(allCVEs.map(c => c.type || "Update"))).sort();

    sources.forEach(s => {
        const option = document.createElement("option");
        option.value = s;
        option.textContent = s;
        sourceSelect.appendChild(option);
    });

    types.forEach(t => {
        const option = document.createElement("option");
        option.value = t;
        option.textContent = t;
        typeSelect.appendChild(option);
    });
}

// ------------------ Render CVEs ------------------
function renderCVEs(cves) {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    cves.sort((a, b) => new Date(b.publishedDate || 0) - new Date(a.publishedDate || 0));

    cves.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";

        const type = cve.type || "Update";
        const badge = `<span class="badge ${type}">${type}</span>`;

        div.innerHTML = `
            ${badge}
            <h3>${cve.id || "N/A"}</h3>
            <p>${cve.description || "No description available"}</p>
            <small>${cve.publishedDate ? new Date(cve.publishedDate).toLocaleString() : ""} | ${cve.source || "Unknown"}</small>
        `;
        container.appendChild(div);
    });
}

// ------------------ Filters ------------------
document.getElementById("filter-source").addEventListener("change", applyFilters);
document.getElementById("filter-type").addEventListener("change", applyFilters);
document.getElementById("search").addEventListener("input", applyFilters);

function applyFilters() {
    const searchTerm = document.getElementById("search").value.toLowerCase();
    const source = document.getElementById("filter-source").value;
    const type = document.getElementById("filter-type").value;

    const filtered = allCVEs.filter(cve => {
        const matchesSearch = (cve.id || "").toLowerCase().includes(searchTerm) ||
                              (cve.description || "").toLowerCase().includes(searchTerm);
        const matchesSource = !source || (cve.source || "Unknown") === source;
        const matchesType = !type || (cve.type || "Update") === type;
        return matchesSearch && matchesSource && matchesType;
    });

    renderCVEs(filtered);
}

// ------------------ Dark Mode ------------------
document.getElementById("dark-mode-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark");
});

// ------------------ Init ------------------
loadCachedCVEs();
