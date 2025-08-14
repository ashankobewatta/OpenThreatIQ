let threats = [];
const modal = new bootstrap.Modal(document.getElementById('threatModal'));

async function fetchThreats() {
    const res = await fetch("/api/threats");
    threats = await res.json();
    populateFilters();
    displayThreats();
}

function populateFilters() {
    const sources = new Set();
    const types = new Set();
    threats.forEach(t => { sources.add(t.source || "Unknown"); types.add(t.type || "Unknown"); });

    const sourceFilter = document.getElementById("sourceFilter");
    const typeFilter = document.getElementById("typeFilter");

    sourceFilter.innerHTML = '<option value="">All</option>';
    typeFilter.innerHTML = '<option value="">All</option>';

    sources.forEach(s => { sourceFilter.innerHTML += `<option value="${s}">${s}</option>`; });
    types.forEach(t => { typeFilter.innerHTML += `<option value="${t}">${t}</option>`; });
}

function displayThreats() {
    const container = document.getElementById("threat-container");
    container.innerHTML = "";
    const search = document.getElementById("searchInput").value.toLowerCase();
    const source = document.getElementById("sourceFilter").value;
    const type = document.getElementById("typeFilter").value;
    const read = document.getElementById("readFilter").value;

    threats
        .filter(t => (!source || t.source === source))
        .filter(t => (!type || t.type === type))
        .filter(t => (read === "" || t.read_flag.toString() === read))
        .filter(t => t.title.toLowerCase().includes(search) || t.description.toLowerCase().includes(search))
        .forEach(t => {
            const col = document.createElement("div");
            col.className = "col";

            const card = document.createElement("div");
            card.className = `card p-3 ${t.read_flag ? "read" : "unread"}`;
            card.innerHTML = `
                <h5>${t.title}</h5>
                <div>
                    <span class="badge bg-info">${t.source}</span>
                    <span class="badge bg-secondary">${t.type}</span>
                    <small>${new Date(t.published_date).toLocaleString()}</small>
                </div>
            `;

            card.addEventListener("click", async () => {
                document.getElementById("threatModalLabel").innerText = t.title;
                document.getElementById("threatModalBody").innerHTML = t.description;
                modal.show();
                if (!t.read_flag) {
                    await fetch(`/api/mark_read/${t.id}`);
                    t.read_flag = 1;
                    card.classList.remove("unread");
                    card.classList.add("read");
                }
            });

            col.appendChild(card);
            container.appendChild(col);
        });
}

// Event listeners
document.getElementById("sourceFilter").addEventListener("change", displayThreats);
document.getElementById("typeFilter").addEventListener("change", displayThreats);
document.getElementById("readFilter").addEventListener("change", displayThreats);
document.getElementById("searchInput").addEventListener("input", displayThreats);

// Dark mode toggle
document.getElementById("darkModeToggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

fetchThreats();
