1.3 Smart Forecasting
Was es bringt: Prognose des Kontostands für nächste 3-6 Monate basierend auf Mustern

Komplexität: High

Integration:

Service: BalanceForecaster
Algorithmus:
Durchschnittliche monatliche Ausgaben/Einnahmen (letzte 6 Monate)
Berücksichtigung erkannter recurring transactions
Saisonale Trends (z.B. Weihnachten)
Frontend: Forecast-Chart im Dashboard
Technisch:

Passt gut: ⚠️ Komplex, aber hochwertig. Benötigt min. 3 Monate Historie


🎨 2. UX / UI VERBESSERUNGEN
2.1 Advanced Filters & Saved Views
Was es bringt: Komplexe Filterabfragen speichern und wiederverwenden

Komplexität: Medium

Integration:

Backend: SavedFilter Tabelle (user_id, name, filter_json)
Frontend: Filter-Builder UI + Schnellzugriff-Buttons
Zustand: LocalStorage + optional Backend-Sync
Beispiel:

"Große Ausgaben > 100€"
"Uncategorized transactions"
"Weihnachtseinkäufe 2024"
Passt gut: ✅ Sehr nützlich für Power-User

2.4 Comparison View
Was es bringt: Monate/Jahre vergleichen (z.B. Dezember 2024 vs. 2023)

Komplexität: Medium

Integration:

Backend: DataAggregator erweitern um comparison-Modus
Frontend: Neue Comparison-Page mit Side-by-Side-Charts
Parameter: period1, period2
Technisch:

Passt perfekt: ✅ Nutzt bestehende Aggregationen

2.5 Export Reports (PDF/Excel)
Was es bringt: Professionelle Reports für Steuern/Buchhaltung

Komplexität: Medium

Integration:

Backend: Libraries (reportlab für PDF, openpyxl für Excel)
Router: /api/v1/reports/export
Frontend: Export-Button mit Format-Wahl
Technisch:

Passt gut: ⚠️ Zusätzliche Dependencies, aber hoher Business-Wert

3.6 Import History & Rollback
Was es bringt: Sehen welche CSVs wann importiert wurden, Rückgängig machen

Komplexität: Low-Medium

Integration:

Neue Tabelle: ImportHistory (filename, uploaded_at, row_count, account_id)
Link: DataRow → import_id
Backend: Rollback = DELETE WHERE import_id = X
Frontend: Import-Log-Page
Technisch:

Passt perfekt: ✅ Wichtig für Fehlerkorrektur

4.2 Account Types (Checking, Savings, Credit Card)
Was es bringt: Unterschiedliche Behandlung je nach Typ

Komplexität: Low

Integration:

Account: account_type ENUM
Logik:
Savings: Exclude from daily cash flow
Credit Card: Invert amounts (positive = spending)
Frontend: Icons/Badges pro Typ
Technisch:

Passt perfekt: ✅ Einfach, praktisch

4.3 Inter-Account Transfers
Was es bringt: Überweisungen zwischen eigenen Konten markieren (nicht als Einnahme/Ausgabe zählen)

Komplexität: Medium

Integration:

Neue Tabelle: Transfer (from_data_row_id, to_data_row_id)
Service: TransferMatcher findet matching transactions (gleiches Datum, invertierter Betrag)
Aggregation: Exclude transfers from income/expense
Frontend: "Transfer"-Badge
Technisch:

Passt perfekt: ✅ Kritisch für korrekte Statistiken bei Multi-Account

5.2 Anomaly Detection
Was es bringt: Ungewöhnliche Ausgaben erkennen (z.B. 500€ für Lebensmittel)

Komplexität: Medium

Integration:

Service: AnomalyDetector
Algorithmus: Z-Score oder IQR-basiert
Berechne pro Kategorie: mean, stddev
Flag: amount > mean + 2*stddev
Dashboard: "Ungewöhnliche Transaktionen"-Widget
Technisch:

Passt gut: ⚠️ Braucht genug Historie (min. 20 Transaktionen pro Kategorie)

5.5 Spending Insights & Tips
Was es bringt: Personalisierte Insights ("Du gibst 30% mehr für Lebensmittel aus als letzten Monat")

Komplexität: Medium

Integration:

Service: InsightsGenerator
Algorithmen:
MoM/YoY Vergleiche
Top-Wachstums-Kategorien
Spar-Potenzial ("Kündige ungenutztes Spotify Abo")
Frontend: Insights-Card im Dashboard
Technisch:

Passt perfekt: ✅ Hoher Wow-Faktor, mittlerer Aufwand

7.3 API Documentation (Swagger/OpenAPI)
Was es bringt: Interaktive API-Docs

Komplexität: Very Low

Integration:

FastAPI: Automatisch verfügbar unter /docs
Erweitern: Bessere Descriptions, Examples
Technisch:

Passt perfekt: ✅ Quasi gratis durch FastAPI

7.4 Database Migration System Improvements
Was es bringt: Saubere Forward/Rollback-Migrations

Komplexität: Low

Integration:

Aktuell: Custom Migrations in /migrations
Besser: Alembic (SQLAlchemy Standard)
Autogenerate Migrations von Model-Änderungen
Technisch:

Passt perfekt: ✅ Professionalisierung

7.5 Logging & Monitoring
Was es bringt: Fehler-Tracking, Performance-Monitoring

Komplexität: Low-Medium

Integration:

Backend: Strukturiertes Logging (Python logging)
Optional: Sentry für Error Tracking
Metrics: Prometheus + Grafana (für Production)
Technisch:

Passt gut: ⚠️ Essential für Production, aber Overhead

7.6 Docker Production Optimization
Was es bringt: Multi-stage builds, Health checks, Log rotation

Komplexität: Low

Integration:

Dockerfile: Multi-stage (builder + runtime)
Compose: Health checks (bereits vorhanden!)
Logs: Fluentd oder ELK Stack
Technisch:

Status: ✅ Bereits gut umgesetzt!