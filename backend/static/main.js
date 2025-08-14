let cvesData = []; // Store fetched CVEs

async function fetchCVEs() {
    const response = await fetch("/api/cves");
    cvesData = await response.json();
    renderCVEs(cvesData);
}

function renderCVEs(data) {
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    data.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";
        div.innerHTML = `<h3>${cve.id}</h3><p>${cve.description}</p><small>${cve.publishedDate}</small>`;
        container.appendChild(div);
    });
}

// Search CVEs
document.getElementById("search-input").addEventListener("input", () => {
    const keyword = document.getElementById("search-input").value.toLowerCase();
    const filtered = cvesData.filter(cve =>
        cve.id.toLowerCase().includes(keyword) ||
        cve.description.toLowerCase().includes(keyword)
    );
    renderCVEs(filtered);
});

// Sort CVEs
document.getElementById("sort-select").addEventListener("change", () => {
    const option = document.getElementById("sort-select").value;
    let sorted = [...cvesData];
    sorted.sort((a, b) => {
        const dateA = new Date(a.publishedDate);
        const dateB = new Date(b.publishedDate);
        return option === "newest" ? dateB - dateA : dateA - dateB;
    });
    renderCVEs(sorted);
});

// Filter by date
document.getElementById("filter-btn").addEventListener("click", () => {
    const start = document.getElementById("start-date").value;
    const end = document.getElementById("end-date").value;

    const filtered = cvesData.filter(cve => {
        const pubDate = new Date(cve.publishedDate);
        const startDate = start ? new Date(start) : null;
        const endDate = end ? new Date(end) : null;

        if (startDate && pubDate < startDate) return false;
        if (endDate && pubDate > endDate) return false;
        return true;
    });
    renderCVEs(filtered);
});

// Reset filters
document.getElementById("reset-btn").addEventListener("click", () => {
    document.getElementById("search-input").value = "";
    document.getElementById("start-date").value = "";
    document.getElementById("end-date").value = "";
    document.getElementById("sort-select").value = "newest";
    renderCVEs(cvesData);
});

fetchCVEs();
