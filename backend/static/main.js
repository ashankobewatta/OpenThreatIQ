let threats = [];
let darkMode = false;

const modal = new bootstrap.Modal(document.getElementById('detailModal'));

async function fetchThreats() {
    const resp = await fetch("/api/threats");
    threats = await resp.json();
    renderFilters();
    renderThreats();
}

function renderFilters() {
    const sources = new Set();
    const types = new Set();
    threats.forEach(t => {
        sources.add(t.source || "Unknown");
        types.add(t.type || "Unknown");
    });

    const sourceFilter = document.getElementById("sourceFilter");
    sourceFilter.innerHTML = '<option value="">All Sources</option>';
    sources.forEach(s => sourceFilter.innerHTML += `<option value="${s}">${s}</option>`);

    const typeFilter = document.getElementById("typeFilter");
    typeFilter.innerHTML = '<option value="">All Types</option>';
    types.forEach(t => typeFilter.innerHTML += `<option value="${t}">${t}</option>`);
}

function renderThreats() {
    const container = document.getElementById("threatContainer");
    const search = document.getElementById("searchInput").value.toLowerCase();
    const sourceVal = document.getElementById("sourceFilter").value;
    const typeVal = document.getElementById("typeFilter").value;
    const readVal = document.getElementById("readFilter").value;

    container.innerHTML = "";
    threats.forEach(t => {
        if (sourceVal && t.source !== sourceVal) return;
        if (typeVal && t.type !== typeVal) return;
        if (readVal && String(t.read_flag) !== readVal) return;
        if (search && !t.title.toLowerCase().includes(search) && !t.description.toLowerCase().includes(search)) return;

        const div = document.createElement("div");
        div.className = "col-md-6";
        div.innerHTML = `
            <div class="card p-3 ${t.read_flag ? "read" : "unread"}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <span class="badge bg-primary">${t.type || "Unknown"}</span>
                        <span class="badge bg-secondary">${t.source || "Unknown"}</span>
                    </div>
                    <small>${t.published_date}</small>
                </div>
                <h5>${t.title}</h5>
                <p>${t.description.substring(0, 150)}${t.description.length>150?"...":""}</p>
            </div>
        `;
        div.querySelector(".card").onclick = () => showDetail(t);
        container.appendChild(div);
    });
}

function showDetail(t) {
    document.getElementById("modalTitle").innerText = t.title;
    document.getElementById("modalDesc").innerText = t.description;
    document.getElementById("modalLink").href = t.link || "#";
    modal.show();
    if (!t.read_flag) markAsRead(t.id);
}

async function markAsRead(id) {
    await fetch(`/api/mark_read/${id}`, {method: "POST"});
    threats = threats.map(t => t.id===id?{...t, read_flag:1}:t);
    renderThreats();
}

document.getElementById("searchInput").addEventListener("input", renderThreats);
document.getElementById("sourceFilter").addEventListener("change", renderThreats);
document.getElementById("typeFilter").addEventListener("change", renderThreats);
document.getElementById("readFilter").addEventListener("change", renderThreats);

document.getElementById("darkToggle").addEventListener("click", () => {
    darkMode = !darkMode;
    document.body.classList.toggle("dark-mode", darkMode);
});

fetchThreats();
