async function fetchCVEs() {
    const response = await fetch("/api/cves");
    const cves = await response.json();

    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    // Gather unique sources and types for filters
    const sources = new Set();
    const types = new Set();

    cves.forEach(cve => {
        sources.add(cve.source || "Unknown");
        types.add(cve.type || "Unknown");

        const div = document.createElement("div");
        div.className = "cve-card" + (cve.read_flag ? " read" : "");
        div.dataset.id = cve.id;

        div.innerHTML = `
            <h5>${cve.id}</h5>
            <div class="badges">
                <span class="badge bg-primary">${cve.type || "Unknown"}</span>
                <span class="badge bg-secondary">${cve.source || "Unknown"}</span>
            </div>
            <p>${cve.description}</p>
            <small>${cve.published_date}</small>
        `;

        // Make card clickable to toggle read/unread
        div.addEventListener("click", async () => {
            div.classList.toggle("read");
            await fetch(`/api/mark_read/${encodeURIComponent(cve.id)}`, { method: "POST" });
        });

        container.appendChild(div);
    });

    populateFilters([...sources], [...types]);
}

// ------------------ Populate dropdown filters ------------------
function populateFilters(sources, types) {
    const sourceSelect = document.getElementById("source-filter");
    const typeSelect = document.getElementById("type-filter");

    sourceSelect.innerHTML = `<option value="">All Sources</option>` + 
        sources.map(s => `<option value="${s}">${s}</option>`).join("");

    typeSelect.innerHTML = `<option value="">All Types</option>` + 
        types.map(t => `<option value="${t}">${t}</option>`).join("");
}

// ------------------ Filter functionality ------------------
document.getElementById("source-filter").addEventListener("change", filterCVEs);
document.getElementById("type-filter").addEventListener("change", filterCVEs);
document.getElementById("search-input").addEventListener("input", filterCVEs);

function filterCVEs() {
    const sourceVal = document.getElementById("source-filter").value;
    const typeVal = document.getElementById("type-filter").value;
    const searchVal = document.getElementById("search-input").value.toLowerCase();

    document.querySelectorAll(".cve-card").forEach(card => {
        const type = card.querySelector(".badge.bg-primary").textContent;
        const source = card.querySelector(".badge.bg-secondary").textContent;
        const text = card.querySelector("p").textContent.toLowerCase();

        const matches = (!sourceVal || source === sourceVal) &&
                        (!typeVal || type === typeVal) &&
                        (!searchVal || text.includes(searchVal));

        card.style.display = matches ? "block" : "none";
    });
}

fetchCVEs();
