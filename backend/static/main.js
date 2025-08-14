let threats = [];
let modal = new bootstrap.Modal(document.getElementById('threatModal'));

async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    populateFilters();
    displayThreats();
}

function populateFilters() {
    const sourceSet = new Set();
    const typeSet = new Set();
    threats.forEach(t => {
        sourceSet.add(t.source || "Unknown");
        typeSet.add(t.type || "Unknown");
    });
    const sourceFilter = document.getElementById("sourceFilter");
    const typeFilter = document.getElementById("typeFilter");
    sourceFilter.innerHTML = `<option value="">All Sources</option>` + [...sourceSet].map(s => `<option value="${s}">${s}</option>`).join('');
    typeFilter.innerHTML = `<option value="">All Types</option>` + [...typeSet].map(s => `<option value="${s}">${s}</option>`).join('');
}

function displayThreats() {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    const search = document.getElementById("searchInput").value.toLowerCase();
    const sourceF = document.getElementById("sourceFilter").value;
    const typeF = document.getElementById("typeFilter").value;
    const readF = document.getElementById("readFilter").value;

    threats.forEach(t => {
        if (sourceF && t.source !== sourceF) return;
        if (typeF && t.type !== typeF) return;
        if (readF && t.read_flag != readF) return;
        if (search && !t.title.toLowerCase().includes(search) && !t.description.toLowerCase().includes(search)) return;

        const card = document.createElement("div");
        card.className = `card p-3 mb-2 ${t.read_flag ? "read" : "unread"}`;
        card.innerHTML = `
            <h5>${t.title}</h5>
            <div>
                <span class="badge bg-info">${t.type || "Unknown"}</span>
                <span class="badge bg-secondary">${t.source || "Unknown"}</span>
            </div>
            <p>${t.description.slice(0, 150)}${t.description.length>150?"...":""}</p>
        `;
        card.addEventListener("click", async () => {
            // Mark as read
            await fetch(`/api/mark_read/${t.id}`, {method:"POST"});
            t.read_flag = 1;
            displayThreats();

            // Show modal
            document.getElementById("modalTitle").textContent = t.title;
            document.getElementById("modalBody").textContent = t.description;
            document.getElementById("modalLink").href = t.link || "#";
            modal.show();
        });
        container.appendChild(card);
    });
}

// Dark mode toggle
document.getElementById("darkModeToggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

// Filters & search
document.getElementById("searchInput").addEventListener("input", displayThreats);
document.getElementById("sourceFilter").addEventListener("change", displayThreats);
document.getElementById("typeFilter").addEventListener("change", displayThreats);
document.getElementById("readFilter").addEventListener("change", displayThreats);

// Add custom feed
document.getElementById("addFeedBtn").addEventListener("click", async () => {
    const name = document.getElementById("newFeedName").value.trim();
    const url = document.getElementById("newFeedURL").value.trim();
    if (!name || !url) return alert("Enter name and URL");
    await fetch("/api/add_feed", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name,url})});
    document.getElementById("newFeedName").value="";
    document.getElementById("newFeedURL").value="";
    await fetchThreats();
});

// Set cache interval
document.getElementById("cacheInterval").addEventListener("change", async () => {
    const minutes = parseInt(document.getElementById("cacheInterval").value);
    await fetch("/api/set_cache_interval", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({minutes})});
    await fetchThreats();
});

// Initial load
fetchThreats();
