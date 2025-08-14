let allCVEs = [];

// ------------------ Load cached data ------------------
async function loadCachedCVEs() {
    try {
        const response = await fetch("/api/cves");
        allCVEs = await response.json();
        populateFilters();
        renderCVEs(allCVEs);
        updateLastUpdated();
    } catch (e) {
        console.error("Error fetching CVEs from backend", e);
        allCVEs = [];
    }
}

// ------------------ Render CVEs ------------------
function renderCVEs(cves) {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    const readList = JSON.parse(localStorage.getItem("readCVEs") || "[]");

    cves.sort((a,b)=> new Date(b.published_date||0) - new Date(a.published_date||0));

    cves.forEach(cve=>{
        const div = document.createElement("div");
        div.className = "cve-card col";
        if(readList.includes(cve.id)) div.classList.add("read");

        const type = cve.type || "Update";
        const badgeColors = {
            "CVE": "bg-danger",
            "Malware": "bg-warning",
            "Phishing": "bg-info",
            "Exploit": "bg-primary",
            "Update": "bg-secondary"
        };
        const badge = `<span class="badge ${badgeColors[type]||'bg-secondary'}">${type}</span>`;

        div.innerHTML = `
            ${badge}
            <h5>${cve.id || "N/A"}</h5>
            <p>${cve.description || "No description available"}</p>
            <small>${cve.published_date ? new Date(cve.published_date).toLocaleString() : ""} | ${cve.source || "Unknown"}</small>
        `;

        div.addEventListener("click", ()=>{
            if(!readList.includes(cve.id)){
                readList.push(cve.id);
                localStorage.setItem("readCVEs", JSON.stringify(readList));
                div.classList.add("read");
            }
        });

        container.appendChild(div);
    });
}

// ------------------ Populate filters ------------------
function populateFilters() {
    const sourceSelect = document.getElementById("filter-source");
    const typeSelect = document.getElementById("filter-type");

    const sources = Array.from(new Set(allCVEs.map(c => c.source || "Unknown"))).sort();
    const types = Array.from(new Set(allCVEs.map(c => c.type || "Update"))).sort();

    sources.forEach(s => {
        if (![...sourceSelect.options].some(o=>o.value===s)){
            const option = document.createElement("option");
            option.value = s;
            option.textContent = s;
            sourceSelect.appendChild(option);
        }
    });

    types.forEach(t => {
        if (![...typeSelect.options].some(o=>o.value===t)){
            const option = document.createElement("option");
            option.value = t;
            option.textContent = t;
            typeSelect.appendChild(option);
        }
    });
}

// ------------------ Filters ------------------
document.getElementById("filter-source").addEventListener("change", applyFilters);
document.getElementById("filter-type").addEventListener("change", applyFilters);
document.getElementById("search").addEventListener("input", applyFilters);

function applyFilters() {
    const searchTerm = document.getElementById("search").value.toLowerCase();
    const source = document.getElementById("filter-source").value;
    const type = document.getElementById("filter-type").value;

    const filtered = allCVEs.filter(cve => {
        const matchesSearch = (cve.id||"").toLowerCase().includes(searchTerm) ||
                              (cve.description||"").toLowerCase().includes(searchTerm);
        const matchesSource = !source || (cve.source||"Unknown") === source;
        const matchesType = !type || (cve.type||"Update") === type;
        return matchesSearch && matchesSource && matchesType;
    });

    renderCVEs(filtered);
}

// ------------------ Dark Mode ------------------
document.getElementById("dark-mode-toggle").addEventListener("click", ()=>{
    document.body.classList.toggle("dark");
});

// ------------------ Update cache interval ------------------
document.getElementById("update-cache-btn").addEventListener("click", async ()=>{
    const interval = parseInt(document.getElementById("cache-interval").value);
    if(isNaN(interval) || interval < 1) return alert("Invalid interval");

    try {
        const resp = await fetch(`/api/update_cache?minutes=${interval}`);
        if(resp.ok){
            alert("Cache updated!");
            loadCachedCVEs();
        } else {
            alert("Failed to update cache");
        }
    } catch(e){
        console.error("Error updating cache", e);
        alert("Failed to update cache");
    }
});

// ------------------ Last Updated ------------------
function updateLastUpdated(){
    if(allCVEs.length === 0) return;
    const latest = allCVEs.reduce((a,b)=>{
        const da = new Date(a.published_date||0);
        const db = new Date(b.published_date||0);
        return da>db ? a : b;
    });
    document.getElementById("last-updated").textContent = `Last updated: ${latest.published_date ? new Date(latest.published_date).toLocaleString() : "Unknown"}`;
}

// ------------------ Initialize ------------------
loadCachedCVEs();
