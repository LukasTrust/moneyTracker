# Verbesserungen & neue Features — Umsetzungsvorschläge

Dieses Dokument listet priorisierte Verbesserungen, Architektur- und Sicherheits-Optimierungen sowie mögliche neue Features für das Projekt `moneyTracker`. Zu jedem Eintrag gibt es eine kurze Motivation, einen konkreten Umsetzungsplan (Schritte, Dateien/Module, Tests) und Hinweise, wie Breaking Changes vermieden werden.

---

## 6) API Design: Pagination & Limits
- Motivation: Viele Endpunkte liefern potenziell große Listen.
- Ziel: Konsistente Pagination (limit/offset) mit vernünftigen Max-Limits; Cursor-based optional.
- Umsetzungsschritte:
  1. Standardisiere Query-Parameter `limit` (default 50) und `offset`, setze `max_limit` z. B. 1000 im Server.
  2. Documentiere in OpenAPI (response_model) Paginierte Responses (data,total,page,pages,limit).
  3. Überprüfe Endpunkte, die `.all()` auf große Tabellen ausführen (z. B. `recategorize` sollte selektiv oder batched sein).
- Dateien/Module:
  - Router-Endpunkte in `backend/app/routers/*.py` (z. B. `/transactions`, `/dashboard/transactions` bereits paginiert)
- Breaking-Change-Risiko: gering (API bleibt kompatibel, solange Defaults beibehalten werden).

---

## 7) Frontend: Typisierung (TS-Migration) & Lint
- Motivation: Typensicherheit erhöht Wartbarkeit; konsistente Code-Qualität.
- Ziel: Schrittweise Migration zu TypeScript, strikt konfiguriertes ESLint + Prettier.
- Umsetzungsschritte:
  1. Führe ESLint-Regeln ein (oder strengere Regeln) und einen `lint`-CI-Check (bereits `eslint` im Projekt).
  2. Schrittweise Migration: beginne mit `src/services` und `src/store` → benenne `.js/.jsx` zu `.ts/.tsx` und ergänze `tsconfig.json`.
  3. Alternativ: Wenn Migration zu TS zu groß, füge JSDoc-Typen hinzu und aktiviere `checkJs` in `tsconfig`.
  4. Teste `vitest`-Läufe während Migration.
- Dateien/Module:
  - `frontend/src/**/*`, `package.json` (devDependencies ggf. anpassen)
- Breaking-Change-Risiko: mittel (bei Umbenennung von Filenamen), schrittweise und branchbasiert durchführen.

---

## 8) Frontend: State Management & Data Fetching
- Motivation: Zustand zentral, Caching, Fehlerbehandlung, Optimistic Updates.
- Ziel: Definierte Services (already exist) + stärkere Fehlergrenzen (Error Boundaries) und einheitliches toast/notification handling.
- Umsetzungsschritte:
  1. Prüfe `zustand`-Store-Struktur (z. B. `categoryStore`) auf Konsistenz; bereits nutzt Optimistic Updates.
  2. Extrahiere gemeinsame `useApi` Hook für Fetching/Loading/Error-Handling (falls noch nicht vorhanden).
  3. Füge Error Boundaries (React) zu wichtigen Seiten (Dashboard, AccountDetail).
- Dateien/Module:
  - `frontend/src/store/*`, `frontend/src/services/*`, `frontend/src/components/common/*`
- Breaking-Change-Risiko: gering.

---

## 9) CSV-Import & Data Validation Hardening
- Motivation: CSVs kommen in unterschiedlichen Encodings & Layouts; Sicherheit gegen fehlerhafte Daten.
- Ziel: Robustere Import-Pipeline mit klarer Validierung, Fehler-Reports und background processing für langsame Imports.
- Umsetzungsschritte:
  1. Verwende `pandas.read_csv(..., encoding=..., engine='python')` mit robusten Fallbacks und Stripping.
  2. Validiere Spalten mit Pydantic-Schemas (`app/schemas/csv.py`) bevor Einträge persistiert werden.
  3. Verwende FastAPI BackgroundTasks für größere Imports oder ein Job-Queue (optionaler Schritt: RQ/Celery — wenn keine neuen Frameworks erwünscht, nutze `BackgroundTasks` oder `asyncio.to_thread`).
  4. Biete Feedback an den Client: Import-Status-Endpoint + Import-History (existiert teilweise).
- Dateien/Module:
  - `backend/app/routers/csv_import.py`, `backend/app/services/import_service.py`
- Breaking-Change-Risiko: gering.

---

## 11) Error Handling & API Contracts
- Motivation: Konsistente Fehlerantworten, bessere UX im Frontend.
- Ziel: Einheitliches Error-Model (HTTP status + code + message + details) und automatische Dokumentation via OpenAPI.
- Umsetzungsschritte:
  1. Definiere ein `ErrorResponse` Pydantic-Schema und verwende FastAPI Exception Handlers (e.g. `@app.exception_handler(HTTPException)`).
  2. Standardisiere Backend-Responses (z. B. `{ "success": false, "error": {"code": ..., "message": ...}}`).
  3. Passe Frontend `api`-interceptor an, um Fehler einheitlich zu behandeln und Toasts anzuzeigen.
- Dateien/Module:
  - `backend/app/schemas/common.py`, `backend/app/main.py` (Exception handler)
- Breaking-Change-Risiko: mittel (API-Formatänderung). Empfehlung: Rückwärtskompatibel bleiben und neue Error-Format optional einführen.

---

## 12) Monitoring & Healthchecks
- Motivation: Produktionstauglichkeit (Liveness/Readiness), Metriken.
- Ziel: Health endpoints, Prometheus metrics (optional), Sentry/Crash-Reporting (optional).
- Umsetzungsschritte:
  1. `/health` und `/metrics` Endpoints existieren teilweise; ergänze ggf. readiness/liveness und DB connectivity check.
  2. Optional: Integriere Sentry DSN via env var (nur wenn gewünscht).
- Dateien/Module:
  - `backend/app/main.py`, `backend/app/routers/health.py` (optional)
- Breaking-Change-Risiko: gering.

---