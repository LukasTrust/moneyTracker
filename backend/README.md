# 💰 Money Tracker Backend

FastAPI-basiertes Backend für die Money Tracker Anwendung mit SQLite-Datenbank.

## 🚀 Features

- ✅ **Account Management**: CRUD-Operationen für Konten
- ✅ **CSV Upload**: Flexible CSV-Import-Funktionalität mit Header-Mapping
- ✅ **Category Management**: Automatische Kategorisierung durch Mapping-Regeln
- ✅ **Duplicate Detection**: SHA256-Hash-basierte Duplikaterkennung
- ✅ **Data Aggregation**: Umfassende Statistiken und Visualisierungsdaten
- ✅ **Dashboard API**: Aggregierte Daten über alle Accounts
- ✅ **RESTful API**: Klare und dokumentierte Endpunkte

## 📋 Voraussetzungen

- Python 3.11+
- Docker & Docker Compose (optional)

## 🛠️ Installation

### Option 1: Lokale Installation

```bash
# In das Backend-Verzeichnis wechseln
cd backend

# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env

# Server starten
uvicorn app.main:app --reload
```

### Option 2: Docker

```bash
# Von der Projekt-Root aus:
docker-compose up -d

# Logs ansehen:
docker-compose logs -f backend
```

## 📡 API-Endpunkte

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Accounts
- `GET /api/v1/accounts` - Alle Konten abrufen
- `GET /api/v1/accounts/{id}` - Einzelnes Konto abrufen
- `POST /api/v1/accounts` - Neues Konto erstellen
- `PUT /api/v1/accounts/{id}` - Konto aktualisieren
- `DELETE /api/v1/accounts/{id}` - Konto löschen

### Categories
- `GET /api/v1/categories` - Alle Kategorien abrufen
- `GET /api/v1/categories/{id}` - Einzelne Kategorie abrufen
- `POST /api/v1/categories` - Neue Kategorie erstellen
- `PUT /api/v1/categories/{id}` - Kategorie aktualisieren
- `DELETE /api/v1/categories/{id}` - Kategorie löschen

### Mappings
- `GET /api/v1/accounts/{id}/mappings` - Mappings für Konto abrufen
- `POST /api/v1/accounts/{id}/mappings` - Mappings speichern
- `DELETE /api/v1/accounts/{id}/mappings` - Mappings löschen

### CSV Upload
- `POST /api/v1/accounts/{id}/preview-csv` - CSV Vorschau
- `POST /api/v1/accounts/{id}/upload` - CSV hochladen und importieren

### Data & Statistics
- `GET /api/v1/accounts/{id}/transactions` - Transaktionsdaten (paginiert)
- `GET /api/v1/accounts/{id}/transactions/summary` - Zusammenfassung (Einnahmen/Ausgaben)
- `GET /api/v1/accounts/{id}/transactions/statistics` - Historische Statistiken
- `GET /api/v1/accounts/{id}/transactions/categories` - Kategorie-Aggregation (per account)
- `GET /api/v1/accounts/{id}/transactions/recipients` - Empfänger-Aggregation (per account)

### Dashboard (All Accounts)
- `GET /api/v1/dashboard/summary` - Gesamt-Zusammenfassung
- `GET /api/v1/dashboard/categories` - Kategorie-Daten (alle Accounts)
- `GET /api/v1/dashboard/balance-history` - Historische Saldoentwicklung
- `GET /api/v1/dashboard/transactions` - Transaktionen (alle Accounts)

## 📚 API-Dokumentation

Nach dem Start ist die interaktive API-Dokumentation verfügbar:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗄️ Datenbank-Schema

### Tabellen

**accounts**
- Speichert Kontoinformationen
- Felder: id, name, bank_name, account_number, description, timestamps

**categories**
- Globale Kategorien mit Mapping-Regeln
- Felder: id, name, color, icon, mappings (JSON), timestamps

**mappings**
- CSV-Header zu Standard-Feld Zuordnungen
- Felder: id, account_id, csv_header, standard_field, timestamps

**data_rows**
- Unveränderbare Transaktionsdaten
- Felder: id, account_id, row_hash, data (JSON), category_id, created_at

## 🔧 Konfiguration

Umgebungsvariablen in `.env`:

```env
# Database
DATABASE_URL=sqlite:///./moneytracker.db

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=Money Tracker API
VERSION=1.0.0

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

## 🧪 Testing

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov=app tests/
```

## 📁 Projekt-Struktur

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI App
│   ├── config.py            # Konfiguration
│   ├── database.py          # DB-Setup
│   ├── models/              # SQLAlchemy Models
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── data_row.py
│   │   └── mapping.py
│   ├── schemas/             # Pydantic Schemas
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── data_row.py
│   │   ├── mapping.py
│   │   ├── statistics.py
│   │   └── csv_upload.py
│   ├── routers/             # API Routes
│   │   ├── accounts.py
│   │   ├── categories.py
│   │   ├── data.py
│   │   ├── csv_upload.py
│   │   ├── dashboard.py
│   │   └── mappings.py
│   └── services/            # Business Logic
│       ├── hash_service.py
│       ├── csv_processor.py
│       ├── category_matcher.py
│       └── data_aggregator.py
├── tests/
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🪵 Logging Utility (kurz)

Die Anwendung enthält eine kleine, sofort nutzbare Logging-Utility unter `app.utils`.

Kurze Anleitung:

```py
# Import
from app.utils import get_logger

# Logger holen
log = get_logger(__name__)

log.info("Server startet")
```

Verhalten:
- Standardausgabe ist JSON-formatiert (gut für Docker: `docker logs` zeigt strukturierte Einträge).
- Lokal kannst du hübsche, farbige Logs erhalten mit der Umgebungsvariable `LOG_PRETTY=1`.
- Loglevel steuerbar über `LOG_LEVEL` (z.B. `DEBUG`, `INFO`).

Beispiel (Docker):

```bash
# In Docker: docker-compose up -d
docker-compose logs -f backend
```

## 🔐 Sicherheit

- CORS-Konfiguration für Frontend-Zugriff
- Input-Validierung durch Pydantic
- SQL-Injection-Schutz durch SQLAlchemy ORM
- Duplicate-Detection durch SHA256-Hashing

## 🐛 Troubleshooting

### Port bereits belegt
```bash
# Anderen Port verwenden
uvicorn app.main:app --reload --port 8001
```

### Datenbank zurücksetzen
```bash
# SQLite-Datei löschen
rm moneytracker.db

# Server neu starten (erstellt neue Datenbank)
uvicorn app.main:app --reload
```

### Dependencies-Probleme
```bash
# Virtual Environment neu erstellen
rm -rf venv
python -m venv venv
source venv/bin/activate  # oder venv\Scripts\activate auf Windows
pip install -r requirements.txt
```

## 📝 Lizenz

Dieses Projekt ist für den persönlichen Gebrauch bestimmt.

## 👨‍💻 Entwicklung

Beim Entwickeln empfiehlt sich der Reload-Modus:

```bash
uvicorn app.main:app --reload --log-level debug
```

Dies startet den Server mit automatischem Reload bei Code-Änderungen.
