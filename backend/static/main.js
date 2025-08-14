let cveData = [];

async function fetchCVEs() {
    const resp = await fetch("/api/cves");
    cveData = await resp.json();
    renderCVEs();
    populateFilters();
}

function renderCVEs() {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";
    cveData.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card col";
        if (cve.read_flag) div.classList.add("read");
        div.dataset.id = cve.id;
        div.dataset.source = cve.source || "Unknown";
        div.dataset.type = cve.type || "Unknown";
        div.dataset.read = cve.read_flag ? "read" : "unread";

        div.innerHTML = `
            <div class="card h-100 p-2">
                <div class="card-body">
                    <h5>${cve.id}</h5>
                    <div class="badges mb-1">
                        <span class="badge bg-primary">${cve.type || "Unknown"}</span>
                        <span class="badge bg-secondary">${cve.source || "Unknown"}</span>
                    </div>
                    <p class="cve-preview">${cve.description.substring(0, 120)}...</p>
                    <small>${cve.published_date}</small>
                </div>
            </div>
        `;
        div.addEventListener("click", () => showModal(cve));
        container.appendChild(div);
    });
    filterCVEs();
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
        ${cve.link ? `<a href="${cve.link}" target="_blank">Read Full Article</a>` : ""}
    `;
    const myModal = new bootstrap.Modal(document.getElementById('cveModal'));
    myModal.show();

    if (!cve.read_flag) {
        fetch(`/api/mark_read/${encodeURIComponent(cve.id)}`, { method: "POST" });
        cve.read_flag = true;
        document.querySelector(`[data-id="${cve.id}"]`).classList.add("read");
    }
}

// Filters
["source-filter","type-filter","read-filter"].forEach(id=>{
    document.getElementById(id).addEventListener("change", filterCVEs);
});
document.getElementById("search-input").addEventListener("input", filterCVEs);

function filterCVEs() {
    const sourceVal = document.getElementById("source-filter").value;
    const typeVal = document.getElementById("type-filter").value;
    const readVal = document.getElementById("read-filter").value;
    const searchVal = document.getElementById("search-input").value.toLowerCase();

    document.querySelectorAll(".cve-card").forEach(card=>{
        const matches = (!sourceVal || card.dataset.source===sourceVal)
            && (!typeVal || card.dataset.type===typeVal)
            && (!readVal || card.dataset.read===readVal)
            && (!searchVal || card.querySelector(".cve-preview").textContent.toLowerCase().includes(searchVal));
        card.style.display = matches ? "block" : "none";
    });
}

function populateFilters() {
    const sources = [...new Set(cveData.map(cve => cve.source || "Unknown"))];
    const types = [...new Set(cveData.map(cve => cve.type || "Unknown"))];

    const sourceSelect = document.getElementById("source-filter");
    const typeSelect = document.getElementById("type-filter");
    sourceSelect.innerHTML = '<option value="">All Sources</option>';
    sources.forEach(s=>sourceSelect.innerHTML+=`<option value="${s}">${s}</option>`);
    typeSelect.innerHTML = '<option value="">All Types</option>';
    types.forEach(t=>typeSelect.innerHTML+=`<option value="${t}">${t}</option>`);
}

// Dark mode toggle
document.getElementById("dark-toggle").addEventListener("click", ()=>{
    document.body.classList.toggle("dark-mode");
});

// Update cache interval
document.getElementById("update-cache").addEventListener("click", async ()=>{
    const minutes = document.getElementById("cache-interval").value;
    if (!minutes || isNaN(minutes)) return alert("Enter valid minutes");
    const resp = await fetch("/api/set_cache_interval", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({minutes})
    });
    const data = await resp.json();
    if(data.status==="ok") alert(`Cache refresh set to ${data.minutes} minutes`);
});

// Mark all read
document.getElementById("mark-all-read").addEventListener("click", async ()=>{
    for(const cve of cveData.filter(c=>!c.read_flag)){
        await fetch(`/api/mark_read/${encodeURIComponent(cve.id)}`, { method:"POST" });
        cve.read_flag = true;
    }
    renderCVEs();
});

// Add custom feed
document.getElementById("save-feed").addEventListener("click", async ()=>{
    const url = document.getElementById("feed-url").value;
    const source = document.getElementById("feed-source").value || "User Feed";
    const type = document.getElementById("feed-type").value || "Other";
    if(!url) return alert("Feed URL required");
    const resp = await fetch("/api/add_feed", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({url, source, type})
    });
    const data = await resp.json();
    if(data.status==="ok"){
        alert("Feed added!");
        fetchCVEs();
        bootstrap.Modal.getInstance(document.getElementById('addFeedModal')).hide();
    }
});

fetchCVEs();
