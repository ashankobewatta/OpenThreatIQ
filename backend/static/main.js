let threats = [];
let modal = new bootstrap.Modal(document.getElementById('threatModal'));

async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    populateFilters();
    renderThreats();
}

function populateFilters() {
    const sourceSet = new Set();
    const typeSet = new Set();
    threats.forEach(t => {
        sourceSet.add(t.source || "Unknown");
        typeSet.add(t.type || "Unknown");
    });

    const sourceFilter = document.getElementById("source-filter");
    const typeFilter = document.getElementById("type-filter");

    sourceFilter.innerHTML = '<option value="">All</option>';
    typeFilter.innerHTML = '<option value="">All</option>';

    sourceSet.forEach(s => sourceFilter.innerHTML += `<option value="${s}">${s}</option>`);
    typeSet.forEach(t => typeFilter.innerHTML += `<option value="${t}">${t}</option>`);
}

function renderThreats() {
    const container = document.getElementById("threat-container");
    container.innerHTML = "";
    const sFilter = document.getElementById("source-filter").value;
    const tFilter = document.getElementById("type-filter").value;
    const rFilter = document.getElementById("read-filter").value;
    const searchText = document.getElementById("search-input").value.toLowerCase();

    threats.filter(t => {
        if (sFilter && t.source !== sFilter) return false;
        if (tFilter && t.type !== tFilter) return false;
        if (rFilter && t.read_flag != rFilter) return false;
        if (searchText && !(t.title.toLowerCase().includes(searchText) || t.description.toLowerCase().includes(searchText))) return false;
        return true;
    }).forEach(t => {
        const col = document.createElement("div");
        col.className = "col-md-4 mb-3";
        col.innerHTML = `
        <div class="card threat-card ${t.read_flag ? 'read' : 'unread'}">
            <div class="card-body">
                <h5 class="card-title">${t.title}</h5>
                <p>
                    <span class="badge bg-primary">${t.type || 'Unknown'}</span>
                    <span class="badge bg-secondary">${t.source || 'Unknown'}</span>
                </p>
                <button class="btn btn-sm btn-outline-info view-btn">View</button>
            </div>
        </div>`;
        col.querySelector(".view-btn").addEventListener("click", () => openModal(t));
        container.appendChild(col);
    });
}

function openModal(t) {
    document.getElementById("modalTitle").innerText = t.title;
    document.getElementById("modalDescription").innerText = t.description;
    document.getElementById("modalLink").href = t.link;
    modal.show();

    if (!t.read_flag) {
        fetch("/api/mark_read", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: t.id})
        }).then(() => t.read_flag = 1);
    }
}

document.getElementById("source-filter").addEventListener("change", renderThreats);
document.getElementById("type-filter").addEventListener("change", renderThreats);
document.getElementById("read-filter").addEventListener("change", renderThreats);
document.getElementById("search-input").addEventListener("input", renderThreats);

document.getElementById("toggle-dark").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

fetchThreats();
