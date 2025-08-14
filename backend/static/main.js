// main.js

let cveData = [];
let currentModalId = null;

// Fetch CVEs from backend
async function fetchCVEs() {
    const response = await fetch("/api/cves");
    cveData = await response.json();
    renderCVEs();
    populateFilters();
}

// Render CVE cards
function renderCVEs() {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    const sourceVal = document.getElementById("source-filter").value;
    const typeVal = document.getElementById("type-filter").value;
    const readVal = document.getElementById("read-filter").value;
    const searchVal = document.getElementById("search-input").value.toLowerCase();

    cveData.forEach(cve => {
        // Apply filters
        if ((sourceVal && cve.source !== sourceVal) ||
            (typeVal && cve.type !== typeVal) ||
            (readVal && (cve.read_flag ? "read" : "unread") !== readVal) ||
            (searchVal && !cve.description.toLowerCase().includes(searchVal))) {
            return;
        }

        const div = document.createElement("div");
        div.className = "cve-card";
        if (cve.read_flag) div.classList.add("read");
        div.dataset.id = cve.id;
        div.dataset.read = cve.read_flag ? "read" : "unread";
        div.dataset.source = cve.source;
        div.dataset.type = cve.type;

        div.innerHTML = `
            <h5>${cve.id}</h5>
            <p class="cve-preview">${cve.description.length > 200 ? cve.description.substring(0, 200) + "..." : cve.description}</p>
            <small>${cve.publishedDate}</small>
            <div class="badges"><span class="badge badge-info">${cve.type}</span><span class="badge badge-secondary">${cve.source}</span></div>
        `;

        div.addEventListener("click", () => markAsReadAndShowModal(cve, div));

        container.appendChild(div);
    });
}

// Mark card as read and show modal
function markAsReadAndShowModal(cve, cardDiv) {
    if (!cve.read_flag) {
        fetch("/api/mark_read", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id: cve.id, read: true})
        })
        .then(res => res.json())
        .then(data => {
            cve.read_flag = true;
            cardDiv.dataset.read = "read";
            cardDiv.classList.add("read");
        })
        .catch(err => console.error(err));
    }

    showCveModal(cve);
}

// Show modal with full CVE info
function showCveModal(cve) {
    const modal = document.getElementById("cve-modal");
    document.getElementById("modal-title").innerText = cve.id;
    document.getElementById("modal-source").innerText = `Source: ${cve.source}`;
    document.getElementById("modal-type").innerText = `Type: ${cve.type}`;
    document.getElementById("modal-date").innerText = `Published: ${cve.publishedDate}`;
    document.getElementById("modal-desc").innerText = cve.description;
    modal.style.display = "block";
}

// Close modal
document.getElementById("modal-close").addEventListener("click", () => {
    document.getElementById("cve-modal").style.display = "none";
});

// Populate filter dropdowns
function populateFilters() {
    const sourceSet = new Set();
    const typeSet = new Set();
    cveData.forEach(cve => {
        sourceSet.add(cve.source || "Unknown");
        typeSet.add(cve.type || "Unknown");
    });

    const sourceFilter = document.getElementById("source-filter");
    const typeFilter = document.getElementById("type-filter");
    sourceFilter.innerHTML = "<option value=''>All Sources</option>";
    typeFilter.innerHTML = "<option value=''>All Types</option>";

    [...sourceSet].forEach(src => {
        sourceFilter.innerHTML += `<option value="${src}">${src}</option>`;
    });
    [...typeSet].forEach(t => {
        typeFilter.innerHTML += `<option value="${t}">${t}</option>`;
    });
}

// Event listeners for filters and search
document.getElementById("source-filter").addEventListener("change", renderCVEs);
document.getElementById("type-filter").addEventListener("change", renderCVEs);
document.getElementById("read-filter").addEventListener("change", renderCVEs);
document.getElementById("search-input").addEventListener("input", renderCVEs);

// Dark mode toggle
document.getElementById("dark-toggle").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
});

fetchCVEs();
