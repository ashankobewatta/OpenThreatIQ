let allThreats = [];

async function fetchThreats() {
    const res = await fetch("/api/threats");
    allThreats = await res.json();
    populateFilters();
    renderThreats();
}

function populateFilters() {
    const sourceSelect = document.getElementById("filterSource");
    const typeSelect = document.getElementById("filterType");

    const sources = Array.from(new Set(allThreats.map(t => t.source || "Unknown")));
    const types = Array.from(new Set(allThreats.map(t => t.type || "Unknown")));

    sources.forEach(s => {
        if (![...sourceSelect.options].some(opt => opt.value === s)) {
            const opt = document.createElement("option"); opt.value = s; opt.text = s;
            sourceSelect.appendChild(opt);
        }
    });

    types.forEach(t => {
        if (![...typeSelect.options].some(opt => opt.value === t)) {
            const opt = document.createElement("option"); opt.value = t; opt.text = t;
            typeSelect.appendChild(opt);
        }
    });
}

function renderThreats() {
    const container = document.getElementById("threat-container");
    container.innerHTML = "";
    const sourceFilter = document.getElementById("filterSource").value;
    const typeFilter = document.getElementById("filterType").value;
    const readFilter = document.getElementById("filterRead").value;
    const searchTerm = document.getElementById("searchInput").value.toLowerCase();

    allThreats.filter(t => {
        const matchesSource = !sourceFilter || t.source === sourceFilter;
        const matchesType = !typeFilter || t.type === typeFilter;
        const matchesRead = !readFilter || (readFilter === "read" ? t.read_flag : !t.read_flag);
        const matchesSearch = !searchTerm || t.title.toLowerCase().includes(searchTerm) || t.description.toLowerCase().includes(searchTerm);
        return matchesSource && matchesType && matchesRead && matchesSearch;
    }).forEach(threat => {
        const div = document.createElement("div");
        div.className = `card col-12 p-3 ${threat.read_flag ? 'read' : 'unread'}`;
        const summary = threat.description.length > 150 ? threat.description.slice(0, 150) + "..." : threat.description;

        div.innerHTML = `
            <h5>${threat.title}</h5>
            <p>${summary}</p>
            <span class="badge bg-primary">${threat.type || "Unknown"}</span>
            <span class="badge bg-secondary">${threat.source || "Unknown"}</span>
            <small>${threat.published_date}</small>
            <div class="mt-2">
                <button class="btn btn-sm btn-info view-more">View More</button>
                <a href="${threat.link}" target="_blank" class="btn btn-sm btn-secondary">Go to Source</a>
            </div>
        `;

        div.querySelector(".view-more").addEventListener("click", () => {
            document.getElementById("modalContent").innerHTML = `
                <h5>${threat.title}</h5>
                <p>${threat.description}</p>
                <p><strong>Source:</strong> ${threat.source || "Unknown"}</p>
                <p><strong>Type:</strong> ${threat.type || "Unknown"}</p>
                <p><strong>Published:</strong> ${threat.published_date}</p>
                <a href="${threat.link}" target="_blank">View Original</a>
            `;
            const modal = new bootstrap.Modal(document.getElementById('threatModal'));
            modal.show();
            markRead(threat.id);
            div.classList.remove('unread'); div.classList.add('read');
        });

        container.appendChild(div);
    });
}

// Event listeners
document.getElementById("filterSource").addEventListener("change", renderThreats);
document.getElementById("filterType").addEventListener("change", renderThreats);
document.getElementById("filterRead").addEventListener("change", renderThreats);
document.getElementById("searchInput").addEventListener("input", renderThreats);

document.getElementById("darkModeToggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

async function markRead(id) {
    await fetch(`/api/mark_read/${id}`);
}

fetchThreats();
