let cvesData = [];

async function fetchCVEs() {
    const response = await fetch("/api/cves");
    cvesData = await response.json();

    // Filter out invalid entries
    cvesData = cvesData.filter(cve => cve.id && cve.description && cve.source && cve.type);

    populateFilters();
    renderCVEs();
}

function populateFilters() {
    const sources = ["all", ...new Set(cvesData.map(cve => cve.source || "Unknown"))];
    const types = ["all", ...new Set(cvesData.map(cve => cve.type || "Unknown"))];

    document.getElementById("source-filter").innerHTML =
        sources.map(s => `<option value="${s}">${s}</option>`).join("");

    document.getElementById("type-filter").innerHTML =
        types.map(t => `<option value="${t}">${t}</option>`).join("");
}

function renderCVEs() {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    // Filters
    const sourceFilter = document.getElementById("source-filter").value;
    const typeFilter = document.getElementById("type-filter").value;
    const searchTerm = document.getElementById("search-bar").value.toLowerCase();

    const filtered = cvesData.filter(cve => {
        return (sourceFilter === "all" || cve.source === sourceFilter) &&
               (typeFilter === "all" || cve.type === typeFilter) &&
               (cve.description.toLowerCase().includes(searchTerm) || cve.id.toLowerCase().includes(searchTerm));
    });

    filtered.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";
        div.innerHTML = `
            <h3>${cve.id}</h3>
            <p>${cve.description}</p>
            <small>${cve.publishedDate} | <span class="badge ${cve.type.toLowerCase()}">${cve.type}</span> | ${cve.source}</small>
        `;
        container.appendChild(div);
    });
}

// Event listeners
document.getElementById("source-filter").addEventListener("change", renderCVEs);
document.getElementById("type-filter").addEventListener("change", renderCVEs);
document.getElementById("search-bar").addEventListener("input", renderCVEs);

fetchCVEs();
