async function fetchCVEs() {
    const response = await fetch("/api/cves");
    const cves = await response.json();

    const container = document.getElementById("cve-container");
    container.innerHTML = "";

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

        div.addEventListener("click", async () => {
            div.classList.toggle("read");
            await fetch(`/api/mark_read/${encodeURIComponent(cve.id)}`, { method: "POST" });
        });

        container.appendChild(div);
    });

    populateFilters([...sources], [...types]);
}

function populateFilters(sources, types) {
    const sourceSelect = document.getElementById("source-filter");
    const typeSelect = document.getElementById("type-filter");

    sourceSelect.innerHTML = `<option value="">All Sources</option>` + sources.map(s => `<option value="${s}">${s}</option>`).join("");
    typeSelect.innerHTML = `<option value="">All Types</option>` + types.map(t => `<option value="${t}">${t}</option>`).join("");
}

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

// Dark mode toggle
document.getElementById("dark-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

// Cache interval update
document.getElementById("update-cache").addEventListener("click", async () => {
    const minutes = document.getElementById("cache-interval").value;
    if (!minutes || isNaN(minutes)) return alert("Enter a valid number");

    const resp = await fetch("/api/set_cache_interval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ minutes })
    });

    const data = await resp.json();
    if (data.status === "ok") alert(`Auto-refresh set to every ${data.minutes} minutes`);
    else alert("Failed to update cache interval");
});

fetchCVEs();
