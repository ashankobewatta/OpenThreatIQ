let threats = [];
let modal = new bootstrap.Modal(document.getElementById('threatModal'));

async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    renderFilters();
    renderThreats();
}

function renderFilters() {
    const sourceSet = new Set();
    const typeSet = new Set();

    threats.forEach(t => {
        sourceSet.add(t.source || "Unknown");
        typeSet.add(t.type || "Unknown");
    });

    const sourceFilter = document.getElementById("sourceFilter");
    const typeFilter = document.getElementById("typeFilter");

    sourceFilter.innerHTML = '<option value="All">All</option>';
    typeFilter.innerHTML = '<option value="All">All</option>';

    Array.from(sourceSet).sort().forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        sourceFilter.appendChild(opt);
    });

    Array.from(typeSet).sort().forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t;
        typeFilter.appendChild(opt);
    });
}

function renderThreats() {
    const container = document.getElementById("threatContainer");
    container.innerHTML = "";

    const searchText = document.getElementById("searchBar").value.toLowerCase();
    const sourceVal = document.getElementById("sourceFilter").value;
    const typeVal = document.getElementById("typeFilter").value;
    const readVal = document.getElementById("readFilter").value;

    threats.forEach(t => {
        // Filters
        if (sourceVal !== "All" && t.source !== sourceVal) return;
        if (typeVal !== "All" && t.type !== typeVal) return;
        if (readVal === "Unread" && t.read_flag) return;
        if (readVal === "Read" && !t.read_flag) return;
        if (searchText && !(t.title.toLowerCase().includes(searchText) || t.description.toLowerCase().includes(searchText))) return;

        const card = document.createElement("div");
        card.className = "col";
        card.innerHTML = `
            <div class="card p-3 ${t.read_flag ? 'read' : 'unread'}">
                <h5>${t.title}</h5>
                <p>${t.description.length > 150 ? t.description.substring(0, 150) + "..." : t.description}</p>
                <div>
                    <span class="badge bg-info">${t.type || 'Unknown'}</span>
                    <span class="badge bg-secondary">${t.source || 'Unknown'}</span>
                    <small class="text-muted">${t.published_date || ''}</small>
                </div>
            </div>
        `;
        // Card click opens modal
        card.querySelector(".card").addEventListener("click", () => openModal(t));
        container.appendChild(card);
    });
}

function openModal(threat) {
    document.getElementById("modalTitle").textContent = threat.title;
    document.getElementById("modalBody").textContent = threat.description;
    document.getElementById("modalLink").href = threat.link || "#";

    if (!threat.read_flag) {
        markRead(threat.id);
        threat.read_flag = 1;
        renderThreats();
    }

    modal.show();
}

async function markRead(id) {
    await fetch(`/api/mark_read/${id}`, { method: "POST" });
}

// Live search
document.getElementById("searchBar").addEventListener("input", renderThreats);

// Filters
document.getElementById("sourceFilter").addEventListener("change", renderThreats);
document.getElementById("typeFilter").addEventListener("change", renderThreats);
document.getElementById("readFilter").addEventListener("change", renderThreats);

// Dark mode toggle
document.getElementById("darkModeToggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

fetchThreats();
