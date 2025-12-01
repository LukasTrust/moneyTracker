**TL;DR**
- Scan der `frontend/src/pages/`-Dateien: `Dashboard.jsx`, `DashboardModern.jsx`, `AccountDetailPage.jsx`, `ComparisonPage.jsx`, `ContractsPage.jsx`, `NotFound.jsx`.
- Fokus: Welche Stores / Hooks / Services jede Seite verwendet und welche Backend-Endpunkte dadurch aufgerufen werden; dokumentiere Abhängigkeiten und mögliche Missmatches gegenüber den Backend-Audits (`audit/06_backend_routers.md` und `audit/06_backend_routers_endpoints.md`).

Methodik
- Gelesen: die Haupt-Seiten-Dateien (sichtbare in `src/pages`). Extrahiert wurden: store hooks (`useAccountStore`, `useFilterStore`, etc.), custom hooks (`useTransactionData`, `useSummaryData`, `useChartData`), and components that may call services (CSV import, ImportHistory, TransferManagement etc.).

Per-Page Findings

- `Dashboard.jsx`
  - Uses: `AccountList`, `CategoryManager`, `DashboardGraphOverview`, `KpiTiles`, `InsightPopup`, `BudgetManager`, `BudgetProgressCard`, `RecurringTransactionsWidget`, `TransferManagementPage`.
  - Stores/Hooks: indirectly uses category and budget hooks via components.
  - Backend endpoints triggered (via components/services):
    - `/accounts` (list) — account list component
    - `/categories` (list) — category manager
    - `/budgets`, `/budgets/progress` — budget widgets
    - `/insights` endpoints — insights popup
    - `/accounts/{id}/recurring-transactions` — recurring widget (per-account optional)
  - Audit cross-check: All of these routers are present in `audit/06_backend_routers.md`. The endpoint reference (`audit/06_backend_routers_endpoints.md`) lists matching endpoints. No direct mismatches found at the page level.

- `AccountDetailPage.jsx`
  - Uses: `useAccountStore` (fetchAccount), `useFilterStore`, hooks from `useDataFetch` (`useTransactionData`, `useSummaryData`, `useChartData`), `CsvImportWizard`, `ImportHistory`, various tab components.
  - Backend endpoints triggered:
    - `/accounts/{id}` — fetchAccount
    - `/accounts/{id}/transactions` — transactions list (via `useTransactionData`)
    - `/accounts/{id}/transactions/summary` — summary
    - `/accounts/{id}/transactions/statistics` — chart data
    - `/csv-import/*` — import preview/import/suggest
    - `/import-history/*` — history, details, rollback
    - category-specific endpoints when using CategoryTab: `/accounts/{id}/categories/{categoryId}/transactions`
  - Audit cross-check: `audit/06_backend_routers_endpoints.md` includes all of these. Important mismatch risk: CSV import contract — frontend invokes `CsvImportWizard.importCsv` and expects immediate completion callback `onImportSuccess`; backend audit recommends async job-based import for large files. Coordinate contract or add file-size limits / job handling in UI.

- `ComparisonPage.jsx`
  - Uses: `ComparisonView` component only (wrapper page).
  - Backend endpoints triggered: depends on `ComparisonView` but typically uses `/comparison/{accountId}` or `/comparison/{accountId}/quick-compare` as per `comparisonService`.
  - Audit cross-check: `comparison` endpoints are mentioned in frontend `comparisonService` and should be covered by backend router MD (if not, add explicit path to `audit/06_backend_routers_endpoints.md`).

- `ContractsPage.jsx` (Contracts / recurring)
  - Uses: recurring transactions widgets and components.
  - Backend endpoints triggered: `/accounts/{id}/recurring-transactions`, `/accounts/recurring-transactions/detect-all`.
  - Audit cross-check: `recurring.py` discussed in routers audit; ensure background job contract for `detect-all` matches UI behavior (the page may trigger detection and expect job status).

- `DashboardModern.jsx`
  - Likely an alternate dashboard layout — uses same components as `Dashboard.jsx`; trigger same endpoints.

- `NotFound.jsx`
  - Static page; no backend calls.

Cross-cutting notes
- CSV Import: multiple pages/components call `/csv-import/*` (preview, suggest, import). Backend audit (`audit/06_backend_routers.md`) recommends server-side limits and background jobs. Pages (e.g., `AccountDetailPage`) currently pass `onImportSuccess` expecting synchronous import completion. Action: either change frontend to accept job-based responses or limit accepted file size and show a progress/job UI.

- Response shape & pagination: many pages use paginated data (transactions). Frontend components expect `{ transactions, total }` or `{ data }` in different places. Backend should standardize via the endpoint reference (`audit/06_backend_routers_endpoints.md`) to `{ items, total }` or update frontend parsing in `src/services/api.js` to normalize.

- Auth & Errors: frontend attaches `Authorization` header; pages expect normalized error messages in `error.response.data.message`. Backend audit suggests a more structured error shape; ensure the api interceptor (`frontend/src/services/api.js`) and backend errors align.

Recommendations (pages-focused)
- Update `CsvImportWizard`/`ImportHistory` usage to handle `{ job_id }` style responses (poll `import-history` for completion) or enforce client-side file limits and show clear error messages when the backend returns an async job response.
- Add a short developer note in `AccountDetailPage.jsx` and `CsvImportWizard` documenting the file-size limit / async job contract once decided.
- Standardize paginated response shape: pick `{ items, total }` and add a small shim in `src/services/api.js` to normalize older shapes.

Next steps
- I can now:
  - A) Create small frontend patches to normalize response shapes in `src/services/api.js`, and add job-polling helper for import jobs, or
  - B) Continue scanning `frontend/src/components/` to collect precise call-sites and event triggers (recommended if you want a full coverage map).

Integration & Cross-References
- **Related audit files:** `/audit/08_frontend_overview.md`, `/audit/09_frontend_src.md`, `/audit/10_frontend_hooks_services.md`, `/audit/12_frontend_components.md`.
- **Pages → Components → Backend mapping:**
  - Many pages embed components that call services directly (e.g., `AccountDetailPage` → `CsvImportWizard` → `/csv-import/*`). When changing CSV import to async jobs, update the page-level UX (onImportSuccess should accept `{ job_id }` and show import progress via `ImportHistory`).
  - `Dashboard` pulls many widgets that rely on `useDashboardData` and `useSummary`; ensure `GET /dashboard` and `GET /dashboard/summary` shapes are documented and lightweight summary endpoints exist for initial render.
- **Recommended page-level actions:**
  1. Add developer notes to `AccountDetailPage.jsx` and `CsvImportWizard.jsx` referencing the CSV import contract and the expected polling workflow (`import-history` endpoints).
  2. Normalize paginated responses at service level so pages don't implement ad-hoc parsing.
  3. Add a small UX pattern for long-running jobs (toast + progress modal + import history link) and document it in `/audit/12_frontend_components.md` under CSV Import.
