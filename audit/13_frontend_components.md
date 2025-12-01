*** Begin Harmonized Components Audit (Frontend) ***

This file collects component-level findings for frontend components and harmonizes section structure: **Files**, **Purpose**, **Observed services/hooks**, **Frontend expectations**, **Risks & notes**, **Recommendations**.

**Accounts**
- **Files:** `frontend/src/components/accounts/AccountList.jsx`, `frontend/src/components/accounts/AccountCard.jsx`, `frontend/src/components/accounts/AccountSettings.jsx`
- **Purpose:** List and manage accounts, show balances and metadata (rename, initial balance, delete).
- **Observed services/hooks:** `useAccountStore` (`fetchAccounts`, `createAccount`, `updateAccount`, `deleteAccount`), `accountService`, `dataService.getSummary(accountId)` returning `summary.current_balance`.
- **Frontend expectations (verify in backend):**
  - `GET /accounts`, `GET /accounts/{id}` return account objects with `id`, `name`, `initial_balance`, `currency`, `created_at`.
  - `POST /accounts`, `PATCH /accounts/{id}`, `DELETE /accounts/{id}` for CRUD operations.
  - `GET /accounts/{id}/summary` (or `GET /data/summary?accountId={id}`) returns `current_balance` and lightweight aggregates used in UI tiles.
- **Risks & notes:**
  - Optimistic updates require consistent error responses and the updated resource for correct rollback behavior.
  - Money handling uses JS numbers; prefer server Decimal or return amounts as strings/cents to avoid float drift.
  - Account deletion can cascade; large deletions should be async to avoid blocking the UI.
- **Recommendations:**
  - Standardize monetary serialization across APIs (string decimal or integer cents) and document in `audit/06_backend_routers_endpoints.md`.
  - Provide a light `GET /accounts/{id}/summary` endpoint for UI tiles.
  - Consider async deletion (`DELETE /accounts/{id}` -> `{ job_id }`) for large data sets.

**Budgets**
- **Files:** `frontend/src/components/budget/BudgetManager.jsx`, `frontend/src/components/budget/BudgetProgressCard.jsx`, `frontend/src/components/budget/index.js`
- **Purpose:** Manage budgets and display progress/summary visualizations used on tabs and dashboards.
- **Observed services/hooks:** `useBudgetStore` (`fetchBudgets`, `createBudget`, `updateBudget`, `deleteBudget`, `fetchBudgetsWithProgress`, `fetchBudgetSummary`), `useCategoryStore` for category metadata.
- **Frontend expectations (verify in backend):**
  - `GET/POST/PATCH/DELETE /budgets` with budget fields (`id`, `category_id`, `amount`, `period`, `start_date`, `end_date`, `description`).
  - Aggregation/progress endpoints: `GET /budgets/progress?accountId=&activeOnly=` or `GET /budgets?with_progress=true` returning `progress` per budget and a `summary` object (`total_budget_amount`, `total_spent`, `total_remaining`, `overall_percentage`).
- **Risks & notes:**
  - Progress aggregations can be heavy; UI polls `BudgetProgressCard` (default 60s). Backend must be performant or provide cached results.
  - Date and numeric consistency matters (use `YYYY-MM-DD` and stable monetary formats).
- **Recommendations:**
  - Document budget endpoints and example responses in `audit/06_backend_routers_endpoints.md`.
  - Offer cached/precomputed progress endpoints or materialized views to reduce runtime aggregation cost.

**Categories**
- **Files:** `frontend/src/components/categories/CategoryManager.jsx`, `frontend/src/components/categories/CategoryMappingEditor.jsx`, `frontend/src/components/categories/CategoryPieChart.jsx`
- **Purpose:** Manage categories, mapping patterns for automatic categorization, and category visualizations.
- **Observed services/hooks:** `useCategoryData`, `categoryService` (`createCategory`, `updateCategory`, `deleteCategory`, `checkPatternConflict`, `removePatternFromCategory`, `recategorizeTransactions`), `CategoryPieChart` for aggregates.
- **Frontend expectations (verify in backend):**
  - Category CRUD: `GET/POST/PATCH/DELETE /categories` supporting `mappings.patterns`.
  - Mapping helpers: `POST /categories/check-pattern`, `POST /categories/remove-pattern` and `POST /categories/recategorize` (or equivalents).
  - Aggregation endpoint for category summaries (fields: `category_id`, `category_name`, `total_amount`, `transaction_count`, `percentage`, `color`).
- **Risks & notes:**
  - Immediate recategorization from UI is expensive; should be asynchronous for large data.
  - Pattern reassignments must be atomic server-side to avoid races.
  - Normalize and index patterns (lowercase/trim) and add DB constraints to prevent duplicates.
- **Recommendations:**
  - Provide `recategorize` as a background job (`{ job_id }`) and a preview endpoint for impact estimation.
  - Debounce mapping saves or require explicit apply/confirm to avoid repeated heavy jobs.
  - Document aggregation payloads used by `CategoryPieChart`.

**Common (UI primitives & Shared Components)**
- **Files:** `frontend/src/components/common/*` (Button, Input, Card, Modal, Toast, LoadingSpinner, Pagination, ErrorBoundary, UnifiedFilter, etc.)
- **Purpose:** Shared primitives used across the app (buttons, inputs, modals, toasts, pagination, unified filter, error boundaries).
- **Observed responsibilities:** Accessibility defaults, focus handling in modals, toast lifecycle via `useUIStore`, pagination contract expectations, and global `UnifiedFilter` state writes.
- **Frontend expectations (verify in backend/store):**
  - `Pagination` expects server metadata (`page`, `page_size`, `total`, `pages`).
  - `UnifiedFilter` shape and keys must match backend query parameters (`fromDate`, `toDate`, `categoryIds`, `recipient`, `purpose`, `transactionType`, `minAmount`, `maxAmount`).
- **Risks & notes:**
  - Global side-effects (document/window) require guarded tests and SSR mocks.
  - Implicit store contracts (UI store, filter store) should be documented to avoid silent breakage.
  - Accessibility: verify focus-trap and aria attributes on `Modal`.
- **Recommendations:**
  - Add docs for store contracts (`useUIStore`, `useFilterStore`) and pagination response shapes.
  - Add tests for `Modal` and `ErrorBoundary` behaviors.
  - Add optional `debounceMs` to `UnifiedFilter` for heavy queries.

**Comparison**
- **Files:** `frontend/src/components/comparison/ComparisonView.jsx`, `ComparisonSummary.jsx`, `ComparisonCharts.jsx`, `CategoryHeatmap.jsx`, `TopRecipientsComparison.jsx`
- **Purpose:** Compare two periods (month/year) with aggregates, deltas, and charts/heatmaps.
- **Observed services/hooks:** `comparisonService.getComparison(accountId, type, period1, period2)` returning `{ period1, period2, comparison, charts, category_heatmap, top_recipients }`.
- **Frontend expectations (verify in backend):**
  - Aggregated comparison payload with `total_income`, `total_expenses`, `current_balance`, `transaction_count`, and per-period series suitable for charting.
- **Risks & notes:**
  - Heavy aggregation — consider precompute/caching keyed by `(accountId, type, period1, period2)`.
- **Recommendations:**
  - Document comparison response shape and cache common queries.

**CSV Import / Upload**
- **Files:** `frontend/src/components/csv/CsvImportWizard.jsx`, `CsvImportMapping.jsx`, `ImportProgress.jsx`, `UploadProgress.jsx`, `BankSelector.jsx`, `ImportHistory.jsx`
- **Purpose:** Multi-step CSV import: preview, header mapping, validation, import results, and history.
- **Observed services/hooks:** `previewCsv(file)`, `importCsv(accountId, mapping, file)`, `mappingService.getMappings(accountId)`, `csvImportApi`.
- **Frontend expectations (verify in backend):**
  - `POST /csv/preview` (multipart) returns `headers`, `sample_rows`, `total_rows` (sync).
  - `POST /csv/import` accepts file+mapping and returns import summary or `job_id` for async processing.
  - Deduplication rules and mapping formats must be documented.
- **Risks & notes:**
  - Large CSV synchronous import risks timeouts and memory; prefer async jobs.
  - UI expects a synchronous summary; if backend returns `job_id` the UI must poll `GET /jobs/{job_id}`.
- **Recommendations:**
  - Keep `previewCsv` synchronous; make full import async (`{ job_id }`) and provide `preview-impact` endpoint.
  - Stream/chunk parsing server-side and document dedupe semantics.

**Dashboard**
- **Files:** `frontend/src/components/dashboard/DashboardGraphOverview.jsx`, `KpiTiles.jsx`, `KpiTile.jsx`, `InsightsCard.jsx`, `InsightPopup.jsx`
- **Purpose:** KPI tiles, balance history, category charts, top recipients/senders and insights.
- **Observed services/hooks:** `useDashboardData(filterParams)`, `dashboardService.getSummary(params)`.
- **Frontend expectations (verify in backend):**
  - `GET /dashboard?{filters}` returning `summary`, `balanceHistory` (series), `categories`, `recipients`, `senders`.
  - `balanceHistory` should be an ordered array of `{ label, income, expenses, balance }` or consistent fields aligned by index.
- **Risks & notes:**
  - Heavy aggregation; cache common queries and provide a small summary endpoint for KPI tiles.
  - Ensure filter param naming and date format consistency with `UnifiedFilter`.
- **Recommendations:**
  - Document `useDashboardData` shape in `audit/06_backend_routers_endpoints.md` and add caching for frequent filter combos.

**Mapping (UI & Services)**
- **Location:** mapping UI is in `categories` and `csv` components; `frontend/src/components/mapping` folder currently empty.
- **Purpose:** Persist and reuse CSV header mappings and text patterns that map to categories/fields.
- **Observed services/hooks:** `mappingService.getMappings(accountId)`, `categoryService.updateCategory(...mappings...)`, `categoryService.checkPatternConflict`, `categoryService.removePatternFromCategory`, `categoryService.recategorizeTransactions`.
- **Risks & notes:**
  - No dedicated mapping folder reduces discoverability; recommend centralizing if feature expands.
  - Pattern conflict transfer must be atomic server-side.
- **Recommendations:**
  - Add dedicated mapping docs (`audit/13_frontend_mapping.md`) and make recategorize async with preview endpoint.

**Recurring**
- **Files:** `frontend/src/components/recurring/RecurringTransactionsList.jsx`, `frontend/src/components/recurring/RecurringTransactionsWidget.jsx`, `frontend/src/hooks/useRecurring.js`
- **Purpose:** Detect and manage recurring transactions; enable toggle/remove and trigger detection.
- **Observed services/hooks:** `useRecurring` (`recurring`, `stats`, `triggerDetection`, `toggleRecurring`, `removeRecurring`).
- **Frontend expectations (verify in backend):**
  - `GET /recurring?accountId=...`, `POST /recurring/detect`, `PATCH /recurring/{id}`, `DELETE /recurring/{id}`.
- **Risks & notes:**
  - Detection is expensive; run full detection as background jobs. Provide preview endpoints.
- **Recommendations:**
  - `POST /recurring/detect` -> `{ job_id }` and `GET /jobs/{job_id}`; add `GET /recurring/preview?pattern=`.

**Tabs**
- **Files:** `frontend/src/components/tabs/BudgetsTab.jsx`, `frontend/src/components/tabs/CategoriesTab.jsx`, `frontend/src/components/tabs/RecipientsTab.jsx`
- **Purpose:** Compose managers & visualizations per domain; rely on shared `UnifiedFilter` and pass `accountId`/`currency` down.
- **Observed integrations:** Tabs call domain hooks (`useCategoryStatistics`, `useRecipientData`, budget hooks) and expect filter-param compatibility with backend query params.
- **Risks & notes:**
  - Shared global filters require consistent naming and date formats; mismatches produce empty charts.
- **Recommendations:**
  - Document filter param names and provide lightweight summary endpoints for tabs.

**Transfers**
- **Files:** `frontend/src/components/transfers/TransferManagementPage.jsx`, `frontend/src/services/transferService.js`
- **Purpose:** Manage detected and linked inter-account transfers; review candidates and create/delete transfers.
- **Observed services/hooks:** `getAllTransfers`, `detectTransfers`, `createTransfer`, `deleteTransfer`.
- **Frontend expectations (verify in backend):**
  - `GET /transfers` (prefer paginated), `POST /transfers/detect`, `POST /transfers`, `DELETE /transfers/{id}`.
- **Risks & notes:**
  - Backend currently returns full list; server-side pagination recommended for scale.
  - Detection is potentially heavy; support async runs with job tracking for full datasets.
- **Recommendations:**
  - Add paginated `GET /transfers` and async `POST /transfers/detect` returning `{ job_id }`.

**Visualization (shared chart components)**
- **Files:** `frontend/src/components/visualization/DataChart.jsx`, `DateRangeFilter.jsx`, `RecipientList.jsx`, `RecipientPieChart.jsx`, `SummaryCards.jsx`, `TransactionTable.jsx`
- **Purpose:** Shared visualization primitives (line/bar charts, pie charts, lists, tables) used across dashboard/tabs.
- **Observed expectations & data shapes:**
  - Charts expect arrays of points with `label` and numeric series (`income`, `expenses`, `balance`).
  - Pie charts expect `{ name|recipient, value|total_amount, count|transaction_count }` and normalize to positive values.
  - Transaction table expects paginated `{ items, total, page, page_size }`.
- **Risks & notes:**
  - Recharts requires numeric values; return consistent numeric types or the UI must reliably convert.
  - Large series should support server-side aggregation/sampling (interval param) to reduce payload and client rendering cost.
- **Recommendations:**
  - Standardize chart payloads and provide `interval` aggregation params (`daily|weekly|monthly`) and `limit`/`page` for tables.
  - Document sign conventions (absolute vs signed amounts) and prefer returning absolute totals for pie charts or provide a query flag `absolute=true`.

---

File harmonized and structure standardized. For any section where you want deeper, per-endpoint JSON examples I can generate concise contract snippets next.

*** End Harmonized Components Audit ***


**Budgets**
- **Files:** `frontend/src/components/budget/BudgetManager.jsx`, `frontend/src/components/budget/BudgetProgressCard.jsx`, `frontend/src/components/budget/index.js`
- **Purpose:** Manage CRUD for budgets (`BudgetManager`) and display budget progress/summary/visualization (`BudgetProgressCard`). Both consume the budget store (`useBudgetStore`) and the category store for category metadata.
- **Store / Service calls observed:**
  - `useBudgetStore` exposes: `budgets`, `fetchBudgets`, `createBudget`, `updateBudget`, `deleteBudget`, `fetchBudgetsWithProgress`, `fetchBudgetSummary`, `budgetsWithProgress`, `summary`.
  - `useCategoryStore` for categories metadata and color/icon lookup.
  - `BudgetManager` calls `fetchBudgets({ force: true })` and `fetchCategories()` on mount; uses `createBudget`, `updateBudget`, `deleteBudget` for mutations.
  - `BudgetProgressCard` calls `fetchBudgetsWithProgress({ activeOnly, accountId })` and `fetchBudgetSummary({ activeOnly, accountId })` and expects `summary` fields like `total_budget_amount`, `total_spent`, `total_remaining`, `overall_percentage`, `budgets_exceeded`, `budgets_at_risk`.
- **Frontend expectations (verify in backend):**
  - CRUD endpoints for budgets (likely `/budgets` and `/budgets/{id}`) that accept/return fields: `id`, `category_id`, `period`, `amount`, `start_date`, `end_date`, `description`.
  - Aggregation endpoints or parameters for progress and summary (e.g. `/budgets/progress` or `/budgets?with_progress=true` and `/budgets/summary`) — frontend expects a structured `progress` object per budget with fields like `spent`, `percentage`, `remaining`, `daily_average_spent`, `projected_total`, `days_remaining`, `is_exceeded`.
  - Support for filtering by `accountId` and `activeOnly` in progress/summary endpoints.
- **Notable behavior / risks:**
  - Numeric handling: frontend uses `parseFloat(budget.amount)` and `.toFixed(2)` for display. Ensure backend provides amounts consistently (Decimal or string) to avoid precision and rounding mismatches.
  - Auto-refresh: `BudgetProgressCard` auto-refreshes on an interval (default 60s). Backend endpoints should be performant for frequent polling or the client should use caching / server-sent events if data is heavy.
  - Heavy aggregation: `fetchBudgetsWithProgress` likely triggers joins and aggregations; for large datasets consider paginating, caching, or returning precomputed progress (materialized view) to keep UI snappy.
- **Recommendations:**
  - Add explicit endpoint documentation in `audit/06_backend_routers_endpoints.md` for budget progress/summary endpoints and the exact JSON shape the UI expects.
  - If aggregations are expensive, add a backend-side cache or scheduled job to precompute `budgets_with_progress` and a light `summary` endpoint for dashboards.
  - Standardize date formats (`YYYY-MM-DD`) and verify timezone handling between UI date inputs and backend storage.
  - Consider returning monetary values as strings or smallest currency unit (cents) to remove floating point ambiguity.

  **Categories**
  - **Files:** `frontend/src/components/categories/CategoryManager.jsx`, `frontend/src/components/categories/CategoryMappingEditor.jsx`, `frontend/src/components/categories/CategoryPieChart.jsx`
  - **Purpose:** Manage global categories, their visual attributes (icon/color), mapping patterns for automatic transaction categorization, and visualizations (pie/bar charts) for category spend analysis.
  - **Store / Service calls observed:**
    - Uses `useCategoryData` (hook) to fetch `categories` (list), and `categoryService` for CRUD + specialized endpoints: `createCategory`, `updateCategory`, `deleteCategory`, `checkPatternConflict`, `removePatternFromCategory`, `recategorizeTransactions`.
    - `CategoryManager` calls `refetch()` after changes and opens `CategoryMappingEditor` for pattern editing.
    - `CategoryMappingEditor` auto-saves mappings (`updateCategory(category.id, { mappings: { patterns } })`) and then calls `categoryService.recategorizeTransactions()` to re-run assignment.
    - `CategoryPieChart` expects aggregated category stats with fields like `category_name`, `total_amount`, `transaction_count`, `percentage`, `color`, `icon`, `category_id`.
  - **Frontend expectations (verify in backend):**
    - Endpoints for category CRUD `/categories` and `/categories/{id}` exist and accept/return `mappings.patterns` arrays.
    - Pattern conflict check endpoint (frontend calls `checkPatternConflict(pattern, categoryId)`) that returns whether a pattern is already assigned and to which category (id, name, color, icon).
    - Endpoint to remove a pattern from another category (`removePatternFromCategory(category_id, pattern)`) and a `recategorizeTransactions` endpoint that triggers reclassification across imported transactions.
    - Aggregation endpoints providing per-category totals and percentages for charting (likely `/data/categories-summary` or `/categories/summary`).
  - **Notable behavior / risks:**
    - Auto-save + immediate recategorization: `CategoryMappingEditor` updates mappings and immediately triggers `recategorizeTransactions()` which may be expensive for large datasets. This is a UX-friendly but heavy operation.
    - Conflict handling: Editor checks conflicts and can remove patterns from other categories; ensure backend enforces atomic transfers to avoid race conditions.
    - Pattern uniqueness / normalization: Patterns are treated case-insensitively and matched as whole words; backend should normalize and index patterns to support fast matching (lowercased, trimmed, word-boundary aware). Consider storing normalized patterns and adding DB-level uniqueness constraints to prevent duplicates across categories.
    - Potential for high write load: Rapid add/remove of patterns by UI can generate many update + recategorize operations; implement debounce, queued background jobs, or rate-limits.
    - Search & matching performance: If recategorization is synchronous, the UI may hang or show errors; prefer background job with job_id and progress polling or incremental reclassification with work queues.
  - **Recommendations:**
    - Move `recategorizeTransactions` to a background job: return `job_id` immediately and let the UI poll status or use WebSocket/SSE for progress updates.
    - Add server-side normalized pattern index and DB constraint to prevent duplicates; expose a clear conflict-check API but enforce uniqueness server-side.
    - Change auto-save to optionally batch changes or debounce rapid updates; only trigger `recategorizeTransactions` after a short idle period or on user confirmation.
    - Provide lightweight endpoints for previewing the impact of a mapping (e.g., `/categories/preview-match?pattern=REWE`) that returns a sample of affected transactions without committing changes.
    - Document the aggregation shape used by `CategoryPieChart` in `audit/06_backend_routers_endpoints.md` to ensure fields match exactly (naming, sign conventions for expenses/income).


**Cross-References & Next Steps**
- **Verify:** Check `audit/06_backend_routers_endpoints.md` for concrete budget and account endpoints; update that file if any expected path/response shape is missing.
- **Actionable quick wins:**
  - Add a note in `audit/00_backend_action_plan.md` to standardize money serialization across API surface.
  - Add a small API contract doc (YAML or JSON examples) for `/accounts` and `/budgets` showing expected request/response payloads.
- **Pending:** Continue scanning `frontend/src/components/categories`, `dashboard`, `transfers`, `csv` and append other sections to this file.

---
**Transfers**
- **Files:** `frontend/src/components/transfers/TransferManagementPage.jsx`, `frontend/src/services/transferService.js`
- **Purpose:** Full-page management UI for detected and linked inter-account transfers: view existing transfers, review detection candidates, auto-create transfers, and unlink/delete transfers.
- **Service / API calls observed:**
  - `getAllTransfers({ include_details })` — currently returns the full list; UI paginates client-side.
  - `detectTransfers(params)` — runs a detection algorithm and returns `candidates`, `total_found`, `auto_created` and possibly per-candidate `confidence_score` and example transactions.
  - `createTransfer(payload)` — creates a transfer/link between two transactions (from/to transaction ids, amount, date, notes).
  - `deleteTransfer(id)` — unlinks/removes an existing transfer.
- **Frontend expectations (verify in backend):**
  - `GET /transfers` or `GET /transfers?include_details=true` returning an array or `{ transfers: [...] }` with fields: `id`, `from_transaction_id`, `to_transaction_id`, `from_account_name`, `to_account_name`, `amount`, `transfer_date`, `is_auto_detected`, `from_transaction`, `to_transaction`.
  - `POST /transfers/detect` accepting detection parameters (e.g., `min_confidence`, `auto_create`) and returning a detection result with `candidates` array and `stats` (total found, auto-created, etc.).
  - `POST /transfers` to create a transfer (or `PUT /transfers/{id}` for updates) and `DELETE /transfers/{id}` to remove.
- **Notable behavior / risks:**
  - Current backend returns all transfers and the UI paginates client-side. This will not scale for many transfers — recommend server-side pagination with `page`, `page_size` and `total` metadata.
  - Detection (`detectTransfers`) may be expensive; if run synchronously it can time out. The UI shows an interactive flow and expects quick results — consider making detection a background job that returns `job_id` and progress, or restrict detection to a sampled window for interactive runs and offer a full background detection for larger datasets.
  - `createTransfer` touches relationships between transactions — ensure database constraints and transactional safety so transfers cannot be duplicated and the same transaction isn't linked twice unless explicitly allowed.
  - Monetary values are formatted with `.toFixed(2)` on the client; ensure backend returns values in a stable numeric/string format (prefer strings or integer cents) to avoid rounding drift.
- **Recommendations:**
  - Add paginated `GET /transfers` with `page`, `page_size`, `total` metadata; update UI to prefer server pagination for large datasets.
  - Implement detection as an async job for full runs: `POST /transfers/detect` -> `{ job_id }`, `GET /jobs/{job_id}` for progress/results. Keep a fast interactive detect sample-mode for immediate feedback.
  - Make `createTransfer` idempotent or return a conflict status when attempting duplicate links; validate that `from_transaction_id` and `to_transaction_id` are not already linked unless re-linking is intended.
  - Document the exact JSON shapes used by `transferService` in `audit/06_backend_routers_endpoints.md`.

**Visualization**
- **Files:** `frontend/src/components/visualization/DataChart.jsx`, `DateRangeFilter.jsx`, `RecipientList.jsx`, `RecipientPieChart.jsx`, `SummaryCards.jsx`, `TransactionTable.jsx`
- **Purpose:** Reusable visualization primitives and composed visualizations used across dashboard, pages and tabs: line/bar charts, pie charts, responsive containers, custom tooltips and legends, summary cards and transaction tables.
- **Observed expectations & data shapes:**
  - `DataChart` expects `data` as an array of objects with `label` and optional numeric fields: `income`, `expenses`, `balance`. Chart components assume consistent array length and aligned labels.
  - `RecipientPieChart` expects items with `{ name|recipient, value|total_amount, count|transaction_count }` and normalizes to positive `value` for charting. It uses Top-5 + "Andere" grouping and computes `percentage` from the total.
  - `SummaryCards` and `TransactionTable` expect lightweight aggregations and paged transaction rows respectively, with consistent date and numeric formats.
- **Frontend expectations (verify in backend):**
  - Endpoints feeding these components should return arrays of series points for charts with `label` and numeric series keys, e.g. `[{ label: '2025-11-01', income: 123.45, expenses: -67.00, balance: 56.45 }, ...]`.
  - Recipient endpoints should return absolute totals (positive) for pie charting or the UI must be aware of sign conventions (pie uses absolute values).
  - Transaction table endpoints should support pagination and sorting parameters and return `{ items: [...], total, page, page_size }`.
- **Notable behavior / risks:**
  - Recharts expects valid numeric values; if backend returns `null`, strings, or inconsistent types, charts can render incorrectly or throw. Normalization logic in `RecipientPieChart` helps, but API contracts should be consistent.
  - `DataChart` formats currency using `value.toFixed(2)` — if values are strings from backend they must be converted safely. Prefer returning numbers (or strings with documented format and conversion step in client hooks).
  - Large time series can be heavy to render on client; backend should support sampling or aggregated buckets (daily/weekly/monthly) via query params to reduce payload size.
  - Tooltip and legend rely on localized formatting; ensure currency and locale metadata are provided or defaulted consistently (UI uses `de-DE`).
- **Recommendations:**
  - Standardize chart payload shapes in `audit/06_backend_routers_endpoints.md` and include example arrays for `balanceHistory`, `categorySeries`, and `recipientSeries`.
  - Add server-side aggregation/sampling options (e.g., `interval=daily|weekly|monthly`) to reduce payload for long ranges.
  - Ensure recipient/recipient-like endpoints return absolute positive numbers for charting or include a documented `absolute=true` query option; document sign conventions.
  - Add lightweight health checks for visualization endpoints and consider caching/ETag support for unchanged series.


File created by codebase audit. Stopped after Accounts + Budgets sections as requested.

**Comparison**
- **Files:** `frontend/src/components/comparison/ComparisonView.jsx`, `ComparisonSummary.jsx`, `ComparisonCharts.jsx`, `CategoryHeatmap.jsx`, `TopRecipientsComparison.jsx`
- **Purpose:** Visual comparison of two time periods (month/year) with summary metrics, charts, heatmap and top recipient comparisons.
- **Service / API calls observed:** Uses `getComparison(accountId, type, period1, period2)` from `comparisonService` which should return an object containing `{ period1, period2, comparison, charts, category_heatmap, top_recipients }` or equivalent.
- **Frontend expectations (verify in backend):**
  - A comparison endpoint that accepts `accountId`, `type` (month|year), and two period identifiers and returns precomputed aggregates for both periods and comparative deltas.
  - Returned numeric fields: `total_income`, `total_expenses` (possibly negative), `current_balance`, `transaction_count`, and `comparison` object with diffs and percent changes.
  - Chart data structures for rendering (time series, category breakdowns), and a category heatmap payload shaped for the `CategoryHeatmap` visualization.
- **Notable behavior / risks:**
  - Heavy aggregation: Comparison queries may be expensive (multiple aggregations across transactions). The backend should either precompute or cache results, or provide an asynchronous job if the data set is very large.
  - Currency/precision: Charts and summary cards format currency with Intl.NumberFormat; ensure backend returns values with stable precision (strings or integers for smallest unit preferred).
  - Defaults & fallbacks: `ComparisonView` will auto-load when `period1`, `period2`, and `accountId` are set. If backend is slow, UX shows loading spinner; consider incremental loading of summary then charts.
- **Recommendations:**
  - Document the exact response shape of `getComparison` in `audit/06_backend_routers_endpoints.md` (fields, nested objects, units).
  - Consider server-side caching keyed by `(accountId, type, period1, period2)` and invalidation when new transactions are imported.

**CSV Import / Upload**
- **Files:** `frontend/src/components/csv/CsvImportWizard.jsx`, `CsvImportMapping.jsx`, `ImportProgress.jsx`, `UploadProgress.jsx`, `BankSelector.jsx`, `ImportHistory.jsx`
- **Purpose:** Multi-step CSV import UI: file upload (drag & drop), header-to-field mapping, preview, validation, import progress and results. Also includes import history and bank/source selection.
- **Service / API calls observed:**
  - `previewCsv(file)` — upload or parse CSV to return `headers`, `sample_rows`, `total_rows`.
  - `importCsv(accountId, mapping, file)` — performs the import and returns result summary: `imported_count`, `duplicate_count`, `error_count`, `recurring_detected`, etc.
  - `mappingService.getMappings(accountId)` — loads saved CSV mappings for an account.
  - `mappingService` and `csvImportApi` are used for conflict checks and persistence.
- **Frontend expectations (verify in backend):**
  - `previewCsv` endpoint that accepts multipart/form-data and returns parsed headers and sample rows without committing data.
  - `importCsv` endpoint that accepts file + mapping and returns structured import results synchronously (or an immediate job id). Frontend currently expects synchronous result object with counts and potential errors.
  - `recategorizeTransactions` may be triggered post-import; ensure the backend either runs this as a fast incremental process or returns a `job_id` and updates status asynchronously.
- **Notable behavior / risks:**
  - Memory / time risk: `importCsv` may require reading and processing large CSVs. Synchronous processing on HTTP request risks timeouts; prefer background processing (enqueue job, return `job_id`) for large files.
  - UX assumptions: Wizard shows simulated stage progress (uploading/parsing/validating/importing) and then expects `importCsv` to finish. If backend returns a `job_id` instead, the UI will need polling or websockets to follow progress.
  - Mapping persistence: Existing mappings are re-used; mismatch handling unlocks mapping editing. Ensure mapping schema is stable (`standard_field`, `csv_header`).
  - Duplicate detection: Backend must provide robust duplicate detection (hashing rows or per-import dedup key). Clarify dedupe rules in API contract.
- **Recommendations:**
  - Move heavy imports to background jobs: `POST /csv-import` returns `{ job_id }`, client polls `/jobs/{job_id}` or listens via SSE/WS for progress. Keep `previewCsv` sync.
  - Provide a `preview-impact` endpoint that shows a small sample of how many rows would match existing mappings, duplicates, and errors, without committing.
  - Standardize mapping format and add endpoint docs in `audit/06_backend_routers_endpoints.md` including `previewCsv` and `importCsv` shapes, error codes, and dedupe semantics.
  - On the backend, stream parsing and deduplication (chunked processing) to avoid loading whole file into memory.

---

File updated by codebase audit: added `Comparison` and `CSV Import` sections.

**Dashboard**
- **Files:** `frontend/src/components/dashboard/DashboardGraphOverview.jsx`, `KpiTiles.jsx`, `KpiTile.jsx`, `InsightsCard.jsx`, `InsightPopup.jsx`
- **Purpose:** Global dashboard overview: KPI tiles, balance history line chart, category pie charts, top recipients/senders, and small insights popups/cards.
- **Service / Hook usage observed:**
  - `useDashboardData(filterParams)` is the primary hook used by `DashboardGraphOverview` to fetch `summary`, `categories`, `balanceHistory`, `recipients`, `senders`, `loading`, `error`.
  - `KpiTiles` directly calls `dashboardService.getSummary(params)` to fetch a lightweight summary for KPI tiles.
  - Charts use `recharts` and expect specific shapes: `balanceHistory` with `labels`, `income`, `expenses`, `balance` arrays; `categories` with `category_name`, `total_amount`, `color`, `icon`, `transaction_count`.
- **Frontend expectations (verify in backend):**
  - Backend provides a dashboard summary endpoint (used by `dashboardService.getSummary`) and a richer `useDashboardData` endpoint that accepts filter params (from `UnifiedFilter`) and returns aggregated structures for charts and leaderboards.
  - Pagination is not required for these aggregate endpoints but filters (accountIds, categoryIds, date range, recipients, search) must be supported.
- **Notable behavior / risks:**
  - Heavy aggregation: dashboard endpoints may perform many aggregations across transactions; consider caching or pre-aggregation for common date ranges.
  - Filter coupling: `DashboardGraphOverview` reads many fields directly from `useFilterStore` and builds `filterParams`. Ensure filter store keys and the backend query parameter names match exactly (e.g., `fromDate`, `toDate`, `accountIds`, `categoryIds`, `recipients`, `search`, `transactionType`, `minAmount`, `maxAmount`, `recipient`, `purpose`).
  - Data shapes: Charts assume arrays of identical length or aligned indices (`balanceHistory.labels` ↔ `balanceHistory.balance` etc.). Backend must guarantee consistent array lengths and ordering.
  - Formatting/units: UI formats currency via `Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })`. Backend should return numeric values compatible with that formatting (strings allowed but prefer numeric or integer cents).
- **Recommendations:**
  - Document the `useDashboardData` response shape in `audit/06_backend_routers_endpoints.md` and add example payloads for `balanceHistory`, `categories`, `recipients`, and `senders`.
  - Add server-side caching for frequent filter combinations and ensure incremental invalidation when new data is imported.
  - Provide a smaller summary endpoint for `KpiTiles` to avoid loading the full dashboard payload when only KPIs are shown.

**Mapping (UI & Services)**
- **Location:** `frontend/src/components/mapping` currently empty. Mapping-related UI and logic are present in:
  - `frontend/src/components/categories/CategoryMappingEditor.jsx` (mapping management and conflict resolution),
  - `frontend/src/components/csv/CsvImportWizard.jsx` (uses `mappingService.getMappings` and persists mapping),
  - `frontend/src/services/mappingService.js` (service layer; inspect for endpoints used).
- **Purpose:** Mapping connects CSV headers and transaction text patterns to canonical internal fields and categories; used for automatic categorization and reuse across imports.
- **Observed service contracts / expectations:**
  - `mappingService.getMappings(accountId)` returns stored mappings for an account.
  - `categoryService.updateCategory(category.id, { mappings: { patterns } })` is used to persist pattern lists.
  - `categoryService.checkPatternConflict(pattern, category.id)` and `categoryService.removePatternFromCategory(category_id, pattern)` are used for conflict detection/transfer.
  - `categoryService.recategorizeTransactions()` is triggered after mapping changes to re-run categorization across existing data.
- **Notable behavior / risks:**
  - No dedicated `mapping` components folder: mappings are implemented across `categories` and `csv` components. This is fine, but centralizing mapping UI or adding an index could improve discoverability.
  - `recategorizeTransactions` is triggered synchronously from the client path; for large data sets this should be a background job (return `job_id`) rather than a blocking API call.
  - `checkPatternConflict` + `removePatternFromCategory` sequence must be atomic server-side to avoid race conditions when two clients attempt to move the same pattern concurrently.
- **Recommendations:**
  - Add a small documentation file `audit/13_frontend_mapping.md` (or expand `audit/12_frontend_components.md`) describing mapping endpoints, payloads and expected side-effects (recategorization behavior). Consider creating a dedicated `mapping` component folder if more UI is added.
  - Make `recategorizeTransactions` asynchronous with job tracking; allow the client to request a preview (impact estimate) before committing large recategorizations.

---

File updated by codebase audit: added `Dashboard` and `Mapping` sections.

**Common**
- **Files:** `frontend/src/components/common/Button.jsx`, `Input.jsx`, `Card.jsx`, `Modal.jsx`, `Toast.jsx`, `LoadingSpinner.jsx`, `Pagination.jsx`, `ErrorBoundary.jsx`, `ErrorMessage.jsx`, `UnifiedFilter.jsx`
- **Purpose:** Shared UI primitives and utilities used across many pages and components: Buttons, Inputs, Cards, Modals/ConfirmDialogs, Toast notifications, Loading skeletons, Pagination controls, global `UnifiedFilter`, and error surface components.
- **Observed responsibilities:**
  - `Button`, `Input`, `Card` provide visual and accessibility defaults (variants, sizes, error states).
  - `Modal` implements focus handling, ESC-to-close, overlay click handling, portal rendering, and a `ConfirmDialog` convenience wrapper.
  - `Toast` reads toasts from `useUIStore` and renders dismissible notifications; several components call `useToast` or UI store to surface messages.
  - `LoadingSpinner` exposes several skeleton helpers (`Skeleton`, `SkeletonLines`, `SkeletonCard`) used by many components for loading states.
  - `Pagination` is used by list views to navigate paged APIs; it expects parent to pass `page`, `pages`, `pageSize`, `total` and handlers.
  - `UnifiedFilter` is the canonical filter UI that writes into the global filter store and is reused widely.
  - `ErrorBoundary` catches render-time exceptions and surfaces an error toast via the UI store; `ErrorMessage` is a reusable inline error box.
- **Frontend expectations / integration notes:**
  - `Modal` uses `createPortal(document.body)` and manipulates `document.body.style.overflow` to prevent scrolling; server-side rendering or tests must mock `document` when rendering.
  - `Toast` relies on `useUIStore` with `toasts` and `removeToast` APIs; ensure the store methods exist and are robust (e.g., deterministic IDs, auto-expire behavior).
  - `Pagination` expects server endpoints that return `total` or `pages` metadata; verify backend endpoints include consistent pagination metadata (page, page_size, total, pages).
  - `UnifiedFilter` updates global filter store on change — many components expect instant effect; ensure stores' initial state is deterministic and persisted where required.
- **Notable behavior / risks:**
  - Global side effects: `Modal` and `ErrorBoundary` both interact with global objects (`document`, `window`). Tests and SSR must be aware or guarded.
  - Implicit contracts: `Toast` and `UnifiedFilter` assume certain store shapes and behavior — mismatches can cause silent UI failures. Keep store types documented.
  - Accessibility: focus-trap and aria attributes are partially present; verify `Modal` focus trapping for keyboard-only users and screen readers. `Button` should ensure `type` defaults avoid unintended form submits (it already sets `button`).
  - Performance: `UnifiedFilter` applies filters immediately on change; for expensive filters consider debouncing or applying on blur to reduce heavy queries.
  - CSS/class dependencies: components rely on Tailwind utility classes and local CSS tokens (e.g., `input`, `label` classes). Ensure global CSS is loaded in `index.html`/`main.jsx`.
- **Recommendations:**
  - Document the store contracts for `useUIStore`, `useFilterStore` and pagination response shapes in `audit/06_backend_routers_endpoints.md` or a dedicated `api_contracts/` folder.
  - Add tests for `Modal` keyboard behavior and `ErrorBoundary` to ensure stable fallback UI and that toasts are emitted as expected.
  - Consider a small `ui/primitives.md` doc describing variant tokens (colors, spacing) and accessibility expectations so new components are consistent.
  - For `UnifiedFilter`, add an optional `debounceMs` prop and document which filter operations are heavy (e.g., text search, category-heavy backend queries).

---
**Recurring**
- **Files:** `frontend/src/components/recurring/RecurringTransactionsList.jsx`, `frontend/src/components/recurring/RecurringTransactionsWidget.jsx`, `frontend/src/components/recurring/index.js`, `frontend/src/hooks/useRecurring.js`
- **Purpose:** List and manage detected recurring transactions (view, toggle active, remove, trigger re-detection). Widget shows condensed stats and monthly estimates.
- **Hook / Service usage observed:**
  - `useRecurring` hook exposes: `recurring`, `stats`, `loading`, `error`, `triggerDetection`, `toggleRecurring(id, enabled)`, `removeRecurring(id)`, `refresh`.
  - UI triggers `triggerDetection()` to re-scan transactions for recurring patterns and calls `toggleRecurring` / `removeRecurring` for per-item actions.
- **Frontend expectations (verify in backend):**
  - Endpoints like `GET /recurring?accountId=...` returning a paginated list of recurring patterns with fields: `id`, `description`, `interval`, `average_amount`, `monthly_amount`, `last_seen`, `enabled`, `examples` (sample transactions).
  - `POST /recurring/detect` or similar to trigger detection; may accept parameters (accountId, window, minOccurrences) and currently the UI expects a near-interactive result.
  - `PATCH /recurring/{id}` to toggle enabled state and `DELETE /recurring/{id}` to remove.
- **Notable behavior / risks:**
  - Detection can be computationally expensive on large datasets. The UI triggers `triggerDetection()` manually; if this is implemented synchronously on the server the request may time out or block other operations.
  - `triggerDetection()` may mutate many transactions if the detection attaches recurring IDs or tags; ensure idempotency and careful transactional boundaries.
  - The widget shows monthly estimates based on average amounts — ensure consistent numeric types (decimals/strings) to avoid rounding issues.
  - Pagination or incremental detection is advisable because displaying very large lists in the UI will be slow.
- **Recommendations:**
  - Implement detection as an asynchronous background job: `POST /recurring/detect` -> returns `{ job_id }`. Provide `GET /jobs/{job_id}` for progress and results. Update UI to poll or use SSE/WS for live updates.
  - Ensure `toggleRecurring` and `removeRecurring` are quick, atomic operations on small, indexed tables; protect detection endpoints with rate-limiting.
  - Add sample endpoint `GET /recurring/preview?pattern=...` to show a few example transactions that would be classified, enabling a lightweight preview before changes.
  - Return monetary values consistently as strings or integer cents to avoid JS float issues.

**Tabs**
- **Files:** `frontend/src/components/tabs/BudgetsTab.jsx`, `frontend/src/components/tabs/CategoriesTab.jsx`, `frontend/src/components/tabs/RecipientsTab.jsx`
- **Purpose:** Simple composition tabs that embed managers and visualizations for budgets, categories and recipients/senders. Each tab reads global `useFilterStore` and passes `accountId` and `currency` props down to children.
- **Observed integrations:**
  - `BudgetsTab` composes `BudgetManager` and `BudgetProgressCard` and expects budget store methods and progress endpoints.
  - `CategoriesTab` (detailed) toggles between `manage` and `analyze` modes, uses `CategoryManager`, `CategoryMappingEditor`, `CategoryPieChart` and hooks `useCategoryData` / `useCategoryStatistics(accountId, params)` for aggregated stats. It expects `refetchCategories()` and `refetchStats()` hooks to exist and be efficient.
  - `RecipientsTab` uses `UnifiedFilter`, `useRecipientData(accountId, params)` and `useSenderData(accountId, params)` to render pie charts and top lists; composes `RecipientPieChart` and `RecipientList`.
- **Frontend expectations (verify in backend):**
  - Category statistics endpoint that accepts granular filter params (date range, categoryIds, min/max amount, recipient/purpose search, transactionType) and returns per-category aggregates and stats object with `totalExpenses`, `totalIncome`, `balance`, `categoriesWithExpenses`, `categoriesWithIncome`.
  - Recipient and sender endpoints that accept similar filters and support `limit` and grouping parameters.
  - Budget progress and summary endpoints supporting `accountId` and `activeOnly` flags.
- **Notable behavior / risks:**
  - Tabs rely on shared `UnifiedFilter` state — mismatches between filter parameter names used in UI and backend query parameter names will cause empty or incorrect aggregations. Ensure parameter naming and date formats are identical (prefer `YYYY-MM-DD`).
  - Some tabs request large aggregations; ensure endpoints support paging or limits where appropriate (e.g., `limit=10`) and return `total` metadata when useful.
  - `CategoriesTab` triggers mapping edits and recategorization flow; ensure recategorization is backgrounded as recommended earlier.
- **Recommendations:**
  - Document the filter parameter names and expected response shapes for category statistics, recipients and senders in `audit/06_backend_routers_endpoints.md`.
  - For heavy aggregation endpoints, provide lightweight summary endpoints and paginated detailed endpoints to keep tab render times short.
  - Add client-side timeouts and user feedback for long-running operations triggered from tabs (e.g., detection, recategorization).


File updated by codebase audit. Categories + Common sections added; Budgets & Accounts already present above.
