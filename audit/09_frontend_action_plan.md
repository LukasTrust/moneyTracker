```markdown
**TL;DR**
- Priorisierte Aktionsliste für das Frontend: Fokus auf Refactorings, Reduktion von Code-Duplikation, API-/Contract-Hardening und kleine ergonomische Änderungen, die das Zusammenspiel mit dem Backend robuster machen.
- Kurzprioritäten (P0..P2):
  - P0: Vereinheitliche Money-Handling (Decimal/strings oder Cents), API-Response-Normalisierung, CSV-Import → async job contract
  - P1: Zentralisiere API-Shims / Normalizer, Job-Poller-Helfer, standardisiere paginierte Responses
  - P2: Extrahiere wiederverwendbare UI-Primitives, debounce UnifiedFilter, Tests & CI für kritische flows

**Zielsetzung**
- Ergebnis: Minimale API-/UI-Inkompatibilitäten, weniger duplicative Logik, besser testbare UI-Schichten, klar definierte contracts mit Backend (CSV import, recategorize jobs, transfers). Priorität auf niedrige Regret-changes (docs, adapters, small refactors) bevor invasive Typ- oder DB-Änderungen.

---

## Top-Prioritäten (konkret, P0)

1) Money serialization & canonical representation
- Problem: Client benutzt JS numbers / .toFixed; Backend nutzt Decimal/NUMERIC → Präzisionsprobleme.
- Aktion: Standardisiere auf serverseitige strings ("123.45") oder integer cents across API. Dokumentiere Entscheidung in `/audit/06_backend_routers_endpoints.md` und passe Frontend-konverter zentral an.
- Dateien (Frontend): `frontend/src/services/api.js` (response normalizer), services die Beträge parsen (z.B. `dataService`, `budgetService`, `accountService`).
- Aufwand: klein (1–2 Tage) — implementiere `parseAmount` / `formatAmount` zentral.

2) CSV import contract: sync vs async
- Problem: UI erwartet synchrone Import-Resultate; Backend-Audit empfiehlt Background-Jobs für große Dateien.
- Aktion: Vereinbare job-based contract: `POST /csv/import` -> `{ job_id }`. Update `csvImportApi.importCsv` so, dass es sowohl eine sync-Antwort als auch `{ job_id }` unterstützt. Implementiere `jobPoller` helper.
- Dateien: `frontend/src/services/csvImportApi.js`, `frontend/src/components/csv/CsvImportWizard.jsx`, `frontend/src/components/csv/ImportProgress.jsx`, neu: `frontend/src/services/jobPoller.js`.
- Aufwand: mittel (2–4 Tage) inkl. UI-Änderungen.

3) Asynchrone Behandlung für teure Operationen (recategorize, transfers.detect)
- Problem: Sofortige Server-Aufrufe können blockieren/timeouten; UI löst sie direkt aus.
- Aktion: Backend sollte `{ job_id }` zurückgeben; Frontend nutzt `jobPoller` und zeigt Fortschritt/Preview. Debounce mapping saves und erfordere explizites Apply.
- Dateien: `frontend/src/components/categories/CategoryMappingEditor.jsx`, `frontend/src/services/categoryService.js`, `frontend/src/services/transferService.js`.
- Aufwand: klein–mittel (2–3 Tage) sofern Backend-Jobs vorhanden.

---

## Key Refactors to Reduce Duplication (P1)

A) Zentraler API-Normalizer
- Implementiere `frontend/src/services/api-normalizer.js` oder erweitere `frontend/src/services/api.js` mit Axios-Interceptors, die:
  - List-Shapes vereinheitlichen auf `{ items: [...], total: N }`
  - Fehler normalisieren zu `{ error: { status, code, message, details } }`
- Alle Service-Wrapper lesen dann nur noch normalisierte Daten.

B) Shared job/polling helper
- Füge `frontend/src/services/jobPoller.js` hinzu mit `waitForJob(jobId)` und `startPolling(jobId, onUpdate, onComplete)`.
- Nutze ihn für CSV-Import, Recategorize und Transfers detection.

C) Konsolidierte Fetch- / Pagination-Hooks
- Neue Hooks: `frontend/src/hooks/useFetchList.js` und `frontend/src/hooks/usePaginated.js`.
- Ziel: Entferne wiederholte Muster (`items`, `loading`, `error`, `page`, `total`) aus Komponenten und ersetze sie durch diese Hooks.

D) Visualisierung: Gemeinsam genutzte Chart-Utilities
- Extrahiere `frontend/src/components/visualization/chart-utils.js` (currency formatting, tooltip components, sampling helpers), um Duplikate in `DataChart` und `RecipientPieChart` zu vermeiden.

E) `UnifiedFilter` Debounce
- Füge prop `debounceMs` hinzu und setze default 300ms. Heavy queries (text search, category filters) sollten debounced werden.

---

## Medium / Nice-to-have (P2)

- Schrittweise Migration kritischer Services/Hooks zu TypeScript oder JSDoc-Typen.
- Einheitliche Date-Utilities: `frontend/src/utils/date.js`.
- Dokumentation: `frontend/docs/API_CONTRACTS.md` und `frontend/docs/UX_JOB_PATTERN.md`.

---

## Quick Wins (low effort, high ROI)

- Centralize `formatCurrency` / `parseAmount` (0.5d).
- Add a shim in `src/services/api.js` to map legacy shapes into `{ items, total }` (0.5–1d).
- Debounce `UnifiedFilter` input changes (0.5d).
- Add `.env.example` + ensure `frontend/.env` not in VCS (0.25d).

---

## Concrete file pointers & small code tasks

- `frontend/src/services/api.js`: add response interceptor to normalize `{ items, total }` and error adapter.
- `frontend/src/services/jobPoller.js`: small utility for polling (exponential backoff optional).
- `frontend/src/components/csv/CsvImportWizard.jsx`: accept `{ job_id }` and open `ImportProgress` modal.
- `frontend/src/components/categories/CategoryMappingEditor.jsx`: debounce saves and add "Apply mappings" flow.
- `frontend/src/components/visualization/*`: move common formatting to `chart-utils.js`.

---

## Estimates & Suggested sequencing

1. API normalizer + format helpers (0.5–1d)
2. `jobPoller` + CSV import non-breaking support (1–2d)
3. Make recategorize/transfers async-friendly + UI changes (2–3d)
4. Consolidate hooks `usePaginated` / `useFetchList` (2–4d)
5. Chart primitives and sampling params (1–2d)

---

## PR checklist (per change)

- Single responsibility per PR.
- Tests for helpers (parsing, normalizer, jobPoller).
- Migration notes for API contract changes.
- Update `/audit` docs when contracts change.

---

## Next immediate actions I can take for you (pick one)

- A) Create the `api-normalizer` + format helpers patch and run quick static checks.
- B) Implement `jobPoller.js` and update `csvImportApi.importCsv` + `CsvImportWizard` to use it (non-breaking: support both sync result and `{ job_id }`).
- C) Generate the `frontend/docs/API_CONTRACTS.md` file listing canonical endpoints / shapes derived from audits.

---

## File created as part of the repository audit
Sag welche Option (A, B oder C) du möchtest und ich setze sie sofort um — ich halte die TODO-Liste synchron.

```