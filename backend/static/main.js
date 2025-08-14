let cvesData = [];

async function fetchCVEs() {
    const response = await fetch("/api/cves");
    cvesData = await response.json();
    populateFilters();
    renderCVEs(cvesData);
}

function renderCVEs(entries) {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    entries.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";
        div.innerHTML = `
            <h3>${cve.id}</h3>
            <p>${cve.description}</p>
            <small>${cve.publishedDate} | ${cve.source} | ${cve.type}</small>
        `;
        container.appendChild(div);
    });
}

function populateFilters() {
    const sources = ["all", ...new Set(cvesData.map(cve => cve.source))];
    const types = ["all", ...new Set(cvesData.map(cve => cve.type))];

    const sourceSelect = document.getElementById("source-filter");
    sourceSelect.innerHTML = sources.map(s => `<option value="${s}">${s}</option>`).join("");

    const typeSelect = document.getElementById("type-filter");
    typeSelect.innerHTML = types.map(t => `<option value="${t}">${t}</option>`).join("");
}

document.getElementById("source-filter").addEventListener("change", applyFilters);
document.getElementById("type-filter").addEventListener("change", applyFilters);
document.getElementById("search-bar").addEventListener("input", applyFilters);

function applyFilters() {
    const source = document.getElementById("source-filter").value;
    const type = document.getElementById("type-filter").value;
    const search = document.getElementById("search-bar").value.toLowerCase();

    let filtered = cvesData;

    if (source !== "all") filtered = filtered.filter(cve => cve.source === source);
    if (type !== "all") filtered = filtered.filter(cve => cve.type === type);
    if (search) filtered = filtered.filter(cve =>
        cve.id.toLowerCase().includes(search) ||
        cve.description.toLowerCase().includes(search)
    );

    renderCVEs(filtered);
}

fetchCVEs();
