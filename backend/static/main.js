document.addEventListener("DOMContentLoaded", () => {
    const cveContainer = document.getElementById("cve-container");
    const searchInput = document.getElementById("search-bar");
    const sourceFilter = document.getElementById("source-filter");
    const typeFilter = document.getElementById("type-filter");
    const readFilter = document.getElementById("read-filter");
    const darkToggle = document.getElementById("dark-toggle");
    const cacheIntervalSelect = document.getElementById("cache-interval");
    const addFeedForm = document.getElementById("add-feed-form");

    let threats = [];

    // Fetch threats from backend
    async function fetchThreats() {
        const res = await fetch("/api/threats");
        threats = await res.json();
        populateFilters();
        renderThreats();
    }

    // Render threat cards
    function renderThreats() {
        const searchTerm = searchInput.value.toLowerCase();
        const sourceVal = sourceFilter.value;
        const typeVal = typeFilter.value;
        const readVal = readFilter.value;

        cveContainer.innerHTML = "";

        threats
            .filter(t => {
                if (sourceVal !== "All" && t.source !== sourceVal) return false;
                if (typeVal !== "All" && t.type !== typeVal) return false;
                if (readVal === "Read" && t.read_flag === 0) return false;
                if (readVal === "Unread" && t.read_flag === 1) return false;
                if (!t.title.toLowerCase().includes(searchTerm) && !t.description.toLowerCase().includes(searchTerm)) return false;
                return true;
            })
            .forEach(t => {
                const card = document.createElement("div");
                card.className = `card ${t.read_flag ? "read" : "unread"}`;
                card.innerHTML = `
                    <div>
                        <span class="badge type-${t.type.replace(/\s+/g,'')}">${t.type}</span>
                        <span class="badge source-badge">${t.source}</span>
                    </div>
                    <h5>${t.title}</h5>
                    <p>${t.description.length > 200 ? t.description.substring(0,200) + " [...]" : t.description}</p>
                    <small>${t.published_date}</small>
                `;

                // Click opens modal with full description
                card.addEventListener("click", () => openModal(t));

                cveContainer.appendChild(card);
            });
    }

    // Populate filters dynamically
    function populateFilters() {
        const sources = ["All", ...new Set(threats.map(t => t.source || "Unknown"))];
        const types = ["All", ...new Set(threats.map(t => t.type || "Unknown"))];

        sourceFilter.innerHTML = sources.map(s => `<option value="${s}">${s}</option>`).join("");
        typeFilter.innerHTML = types.map(t => `<option value="${t}">${t}</option>`).join("");
    }

    // Modal handling
    const modal = document.getElementById("threatModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalBody = document.getElementById("modalBody");
    const modalLink = document.getElementById("modalLink");
    const closeModal = document.getElementById("closeModal");

    function openModal(t) {
        modalTitle.innerText = t.title;
        modalBody.innerText = t.description;
        modalLink.href = t.link || "#";
        modalLink.target = "_blank";
        modal.style.display = "block";

        // Mark read instantly
        if (t.read_flag === 0) {
            fetch(`/api/mark_read/${t.id}`, { method: "POST" })
                .then(() => { t.read_flag = 1; renderThreats(); });
        }
    }

    closeModal.addEventListener("click", () => { modal.style.display = "none"; });
    window.addEventListener("click", e => { if (e.target === modal) modal.style.display = "none"; });

    // Event listeners
    [searchInput, sourceFilter, typeFilter, readFilter].forEach(el => {
        el.addEventListener("input", renderThreats);
        el.addEventListener("change", renderThreats);
    });

    // Dark mode toggle
    darkToggle.addEventListener("change", () => {
        document.body.classList.toggle("dark-mode", darkToggle.checked);
    });

    // Cache interval selection
    cacheIntervalSelect.addEventListener("change", () => {
        const minutes = parseInt(cacheIntervalSelect.value);
        fetch("/api/set_cache_interval", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ minutes })
        });
    });

    // Add custom feed
    addFeedForm.addEventListener("submit", e => {
        e.preventDefault();
        const url = document.getElementById("feed-url").value;
        const source = document.getElementById("feed-source").value || "Custom";
        const type = document.getElementById("feed-type").value || "Unknown";

        fetch("/api/add_feed", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, source, type })
        }).then(res => res.json()).then(data => {
            if (data.status === "ok") {
                fetchThreats();
                addFeedForm.reset();
            } else {
                alert("Error adding feed: " + data.message);
            }
        });
    });

    fetchThreats();
});
