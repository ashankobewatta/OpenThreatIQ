document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("search-input");
    const typeFilter = document.getElementById("type-filter");
    const sourceFilter = document.getElementById("source-filter");
    const readFilter = document.getElementById("read-filter");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const threatsContainer = document.getElementById("threats-container");

    let threatsData = [];

    // Fetch and render threats
    function fetchThreats() {
        fetch("/api/threats")
            .then(res => res.json())
            .then(data => {
                threatsData = data;
                renderThreats();
            })
            .catch(err => console.error("Error fetching threats:", err));
    }

    // Render threat cards
    function renderThreats() {
        threatsContainer.innerHTML = "";
        const searchText = searchInput.value.toLowerCase();
        const typeValue = typeFilter.value;
        const sourceValue = sourceFilter.value;
        const readValue = readFilter.value;

        threatsData
            .filter(t => {
                const matchesSearch =
                    t.title.toLowerCase().includes(searchText) ||
                    t.description.toLowerCase().includes(searchText);

                const matchesType = typeValue === "" || t.type === typeValue;
                const matchesSource = sourceValue === "" || t.source === sourceValue;
                const matchesRead =
                    readValue === "" ||
                    (readValue === "unread" && !t.read) ||
                    (readValue === "read" && t.read);

                return matchesSearch && matchesType && matchesSource && matchesRead;
            })
            .forEach(t => {
                const card = document.createElement("div");
                card.className = `card mb-3 ${t.read ? "read" : "unread"}`;
                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">${t.title}</h5>
                        <span class="badge bg-info">${t.type || "Unknown"}</span>
                        <span class="badge bg-secondary">${t.source || "Unknown"}</span>
                        <p class="card-text">${t.description.substring(0, 150)}${t.description.length > 150 ? "..." : ""}</p>
                        <small class="text-muted">Published: ${t.published}</small>
                    </div>
                `;

                // Click to open full modal
                card.addEventListener("click", () => {
                    markRead(t.id);
                    document.getElementById("modal-title").innerText = t.title;
                    document.getElementById("modal-body").innerText = t.full_description || t.description;
                    document.getElementById("modal-source-btn").href = t.link;
                    new bootstrap.Modal(document.getElementById("detailsModal")).show();
                });

                threatsContainer.appendChild(card);
            });
    }

    // Mark as read instantly
    function markRead(id) {
        const threat = threatsData.find(t => t.id === id);
        if (threat) threat.read = true;
        renderThreats();

        fetch(`/api/mark_read/${id}`, { method: "POST" })
            .catch(err => console.error("Error marking read:", err));
    }

    // Filter & search listeners
    searchInput.addEventListener("input", renderThreats);
    typeFilter.addEventListener("change", renderThreats);
    sourceFilter.addEventListener("change", renderThreats);
    readFilter.addEventListener("change", renderThreats);

    // Dark mode toggle
    darkModeToggle.addEventListener("click", function () {
        document.body.classList.toggle("dark-mode");
        localStorage.setItem("darkMode", document.body.classList.contains("dark-mode"));
    });

    if (localStorage.getItem("darkMode") === "true") {
        document.body.classList.add("dark-mode");
    }

    fetchThreats();
});
