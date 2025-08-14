document.addEventListener("DOMContentLoaded", () => {
    const cveContainer = document.getElementById("cve-container");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const searchInput = document.getElementById("search-input");
    const typeFilter = document.getElementById("type-filter");
    const sourceFilter = document.getElementById("source-filter");
    const readFilter = document.getElementById("read-filter");

    let allThreats = [];

    // Fetch threats from backend
    async function fetchThreats() {
        const res = await fetch("/api/threats");
        allThreats = await res.json();
        populateFilters();
        renderThreats(allThreats);
    }

    // Populate filter dropdowns
    function populateFilters() {
        const types = new Set();
        const sources = new Set();

        allThreats.forEach(t => {
            types.add(t.type || "Unknown");
            sources.add(t.source || "Unknown");
        });

        typeFilter.innerHTML = `<option value="">All Types</option>` +
            Array.from(types).map(t => `<option value="${t}">${t}</option>`).join("");

        sourceFilter.innerHTML = `<option value="">All Sources</option>` +
            Array.from(sources).map(s => `<option value="${s}">${s}</option>`).join("");

        readFilter.innerHTML = `
            <option value="">All</option>
            <option value="read">Read</option>
            <option value="unread">Unread</option>
        `;
    }

    // Render threats to the page
    function renderThreats(threats) {
        cveContainer.innerHTML = "";
        threats.forEach(t => {
            const div = document.createElement("div");
            div.className = `card mb-2 p-3 ${t.read_flag ? "read" : "unread"}`;
            div.innerHTML = `
                <h5>${t.title}</h5>
                <p>${t.description.length > 200 ? t.description.slice(0,200) + "..." : t.description}</p>
                <div class="mb-1">
                    <span class="badge bg-info">${t.type || "Unknown"}</span>
                    <span class="badge bg-secondary">${t.source || "Unknown"}</span>
                </div>
                <small>${t.published_date}</small>
                <button class="btn btn-sm btn-primary view-more mt-2">View More</button>
            `;
            // Handle click to view full description
            div.querySelector(".view-more").addEventListener("click", () => {
                showModal(t);
                if (!t.read_flag) markRead(t.id, div);
            });
            cveContainer.appendChild(div);
        });
    }

    // Modal popup
    function showModal(threat) {
        const modal = document.getElementById("threat-modal");
        document.getElementById("modal-title").innerText = threat.title;
        document.getElementById("modal-source").innerText = threat.source || "Unknown";
        document.getElementById("modal-type").innerText = threat.type || "Unknown";
        document.getElementById("modal-date").innerText = threat.published_date;
        document.getElementById("modal-description").innerText = threat.description;
        document.getElementById("modal-link").href = threat.link || "#";
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // Mark as read instantly
    async function markRead(id, cardDiv) {
        await fetch(`/api/mark_read/${id}`, { method: "POST" });
        cardDiv.classList.remove("unread");
        cardDiv.classList.add("read");
        const threat = allThreats.find(t => t.id === id);
        if (threat) threat.read_flag = 1;
    }

    // Dark mode toggle
    darkModeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
    });

    // Filters and search
    function applyFilters() {
        let filtered = [...allThreats];
        const search = searchInput.value.toLowerCase();
        const type = typeFilter.value;
        const source = sourceFilter.value;
        const read = readFilter.value;

        filtered = filtered.filter(t => {
            const matchesSearch = t.title.toLowerCase().includes(search) || t.description.toLowerCase().includes(search);
            const matchesType = !type || (t.type || "Unknown") === type;
            const matchesSource = !source || (t.source || "Unknown") === source;
            const matchesRead = !read || (read === "read" ? t.read_flag === 1 : t.read_flag === 0);
            return matchesSearch && matchesType && matchesSource && matchesRead;
        });

        renderThreats(filtered);
    }

    searchInput.addEventListener("input", applyFilters);
    typeFilter.addEventListener("change", applyFilters);
    sourceFilter.addEventListener("change", applyFilters);
    readFilter.addEventListener("change", applyFilters);

    fetchThreats();
});
