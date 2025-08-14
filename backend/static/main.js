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

        // Add badge for type
        const badge = `<span class="badge ${cve.type}">${cve.type}</span>`;

        div.innerHTML = `
            <h3>${cve.id} ${badge}</h3>
            <p>${cve.description}</p>
            <small>${cve.publishedDate} | ${cve.source}</small>
        `;
        container.appendChild(div);
    });
}

// Populate source/type filters
function populateFilters() {
    const sources = ["all", ...new Set(cvesData.map(cve => cve.source))];
    const types = ["all", ...new Set(cvesData.map(cve => cve.type))];

    document.getElementById("source-filter").innerHTML = sources.map(s => `<option value="${s}">${s}</option>`).join("");
    document.getElementById("type-filter").innerHTML = types.map(t => `<option value="${t}">${t}</option>`).join("");
}

// Filters & search
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

// Dark mode toggle
document.getElementById("dark-mode-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

fetchCVEs();
