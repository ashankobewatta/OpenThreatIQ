let allCVEs = [];

async function fetchCVEs() {
    const response = await fetch("/api/cves");
    allCVEs = await response.json();
    populateFilters();
    renderCVEs(allCVEs);
}

function populateFilters() {
    const sourceSelect = document.getElementById("filter-source");
    const typeSelect = document.getElementById("filter-type");

    const sources = Array.from(new Set(allCVEs.map(c => c.source))).sort();
    const types = Array.from(new Set(allCVEs.map(c => c.type))).sort();

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

function renderCVEs(cves) {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    // Sort by publishedDate descending
    cves.sort((a, b) => new Date(b.publishedDate) - new Date(a.publishedDate));

    cves.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";
        const badge = `<span class="badge ${cve.type}">${cve.type}</span>`;
        div.innerHTML = `${badge}<h3>${cve.id || "N/A"}</h3>
                         <p>${cve.description || "No description available"}</p>
                         <small>${cve.publishedDate ? new Date(cve.publishedDate).toLocaleString() : ""} | ${cve.source}</small>`;
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
        const matchesSearch = cve.id.toLowerCase().includes(searchTerm) ||
                              cve.description.toLowerCase().includes(searchTerm);
        const matchesSource = !source || cve.source === source;
        const matchesType = !type || cve.type === type;
        return matchesSearch && matchesSource && matchesType;
    });

    renderCVEs(filtered);
}

// ------------------ Dark Mode ------------------
document.getElementById("dark-mode-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark");
});

// ------------------ Init ------------------
fetchCVEs();
