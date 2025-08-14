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
        div.className = "col-lg-4 col-md-6";
        div.innerHTML = `
            <div class="cve-card ${cve.read_flag ? "read" : ""}" data-id="${cve.id}" data-read="${cve.read_flag ? "read" : "unread"}">
                <h5>${cve.id}</h5>
                <div class="badges">
                    <span class="badge bg-primary">${cve.type || "Unknown"}</span>
                    <span class="badge bg-secondary">${cve.source || "Unknown"}</span>
                </div>
                <p class="cve-preview">${cve.description.substring(0, 80)}...</p>
                <small>${cve.published_date}</small>
            </div>
        `;
        const card = div.querySelector(".cve-card");
        card.addEventListener("click", () => showModal(cve));
        container.appendChild(div);
    });

    populateFilters([...sources], [...types]);
}

function showModal(cve) {
    const modalBody = document.getElementById("modal-body-content");
    modalBody.innerHTML = `
        <p><strong>ID:</strong> ${cve.id}</p>
        <p><strong>Type:</strong> ${cve.type}</p>
        <p><strong>Source:</strong> ${cve.source}</p>
        <p><strong>Published Date:</strong> ${cve.published_date}</p>
        <hr>
        <p>${cve.description}</p>
    `;
    const myModal = new bootstrap.Modal(document.getElementById('cveModal'));
    myModal.show();

    fetch(`/api/mark_read/${encodeURIComponent(cve.id)}`, { method: "POST" });
    const cardDiv = document.querySelector(`[data-id="${cve.id}"]`);
    cardDiv.classList.add("read");
    cardDiv.dataset.read = "read";
}

// Filters
document.getElementById("source-filter").addEventListener("change", filterCVEs);
document.getElementById("type-filter").addEventListener("change", filterCVEs);
document.getElementById("read-filter").addEventListener("change", filterCVEs);
document.getElementById("search-input").addEventListener("input", filterCVEs);

function filterCVEs() {
    const sourceVal = document.getElementById("source-filter").value;
    const typeVal = document.getElementById("type-filter").value;
    const readVal = document.getElementById("read-filter").value;
    const searchVal = document.getElementById("search-input").value.toLowerCase();

    document.querySelectorAll(".cve-card").forEach(card => {
        const type = card.querySelector(".badge.bg-primary").textContent;
        const source = card.querySelector(".badge.bg-secondary").textContent;
        const text = card.querySelector("p").textContent.toLowerCase();
        const read = card.dataset.read;

        const matches = (!sourceVal || source === sourceVal) &&
                        (!typeVal || type === typeVal) &&
                        (!readVal || readVal === read) &&
                        (!searchVal || text.includes(searchVal));
        card.parentElement.style.display = matches ? "block" : "none";
    });
}

// Dark mode
document.getElementById("dark-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

// Cache interval
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
});

// Mark all read
document.getElementById("mark-all-read").addEventListener("click", async () => {
    const cards = document.querySelectorAll(".cve-card");
    for (let card of cards) {
        if (!card.classList.contains("read")) {
            const id = card.dataset.id;
            await fetch(`/api/mark_read/${encodeURIComponent(id)}`, { method: "POST" });
            card.classList.add("read");
            card.dataset.read = "read";
        }
    }
});

// Add Custom Feed
document.getElementById("save-feed").addEventListener("click", async () => {
    const url = document.getElementById("feed-url").value;
    const source = document.getElementById("feed-source").value || "User Feed";
    const type = document.getElementById("feed-type").value || "Other";

    if (!url) return alert("Feed URL required");

    const resp = await fetch("/api/add_feed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, type, source })
    });

    const data = await resp.json();
    if (data.status === "ok") {
        alert("Feed added successfully!");
        fetchCVEs();
        const myModal = bootstrap.Modal.getInstance(document.getElementById('addFeedModal'));
        myModal.hide();
    } else alert(data.message || "Failed to add feed");
});

function populateFilters(sources, types) {
    const sourceSelect = document.getElementById("source-filter");
    const typeSelect = document.getElementById("type-filter");

    sourceSelect.innerHTML = '<option value="">All Sources</option>';
    sources.forEach(src => sourceSelect.innerHTML += `<option value="${src}">${src}</option>`);

    typeSelect.innerHTML = '<option value="">All Types</option>';
    types.forEach(t => typeSelect.innerHTML += `<option value="${t}">${t}</option>`);
}

fetchCVEs();
