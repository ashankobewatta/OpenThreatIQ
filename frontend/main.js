async function fetchCVEs() {
    const response = await fetch("/api/cves");
    const cves = await response.json();
    const container = document.getElementById("cve-container");
    container.innerHTML = "";

    cves.forEach(cve => {
        const div = document.createElement("div");
        div.className = "cve-card";
        div.innerHTML = `<h3>${cve.id}</h3><p>${cve.description}</p><small>${cve.publishedDate}</small>`;
        container.appendChild(div);
    });
}

fetchCVEs();
