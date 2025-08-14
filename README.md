# OpenThreatIQ

OpenThreatIQ is an open-source Threat Intelligence Dashboard that aggregates cybersecurity threat data such as CVEs (Common Vulnerabilities and Exposures). The project is designed to be extendable, making it easy for anyone to add more feeds, visualizations, and alerting features.

## Features
- Fetches latest CVEs from the NVD (National Vulnerability Database)
- Caches data locally for faster access
- Displays threat info in a clean web dashboard
- Open-source and easily extendable
- Docker-ready for simple deployment

## Tech Stack
- **Backend:** Python 3 with Flask
- **Frontend:** HTML/CSS/JavaScript
- **Database:** JSON cache (extendable to PostgreSQL or SQLite)
- **Visualization:** Simple frontend cards (can be upgraded with Chart.js or Plotly)
- **Deployment:** Docker and Docker Compose supported

## Folder Structure
```
OpenThreatIQ/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── utils.py
├── frontend/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── data/
│   └── cve_cache.json
├── docker-compose.yml
├── README.md
└── LICENSE
```

## Setup & Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/ashankobewatta/OpenThreatIQ
cd OpenThreatIQ
```

### 2. Install Python dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Flask backend
```bash
python backend/app.py
```

### 4. Open the dashboard
Open your browser and go to:  
```
http://localhost:5000
```

You should see the OpenThreatIQ dashboard displaying the latest CVEs.

---

## Docker Setup

### 1. Build and run with Docker Compose
```bash
docker-compose up --build
```

### 2. Access the dashboard
Open your browser at:  
```
http://localhost:5000
```

---

## Extend the Dashboard

You can add more features easily:
- **Threat Feeds:** Integrate MalwareBazaar, AlienVault OTX, or phishing feeds
- **Charts & Visualizations:** Use Chart.js or Plotly to visualize threat trends
- **Alerts:** Add email or desktop notifications for high-severity CVEs
- **Database:** Replace the JSON cache with PostgreSQL or SQLite for larger datasets

---
