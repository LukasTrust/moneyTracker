```markdown
**TL;DR (deutsch)**
- Gesamt‑Aktionsplan für Repository‑Stabilisierung und kurzfristige Verbesserungen.
- Reihenfolge: Das Backend wird zuerst stabilisiert und zertifiziert; alle Frontend‑Änderungen richten sich an das neue Backend‑Contract‑Set aus. Ziel: geringe Regressions‑Risiken, klarer Migrationspfad, testbare Schritte.

Zielgruppe
- Maintainer Backend, Frontend-Entwickler, DevOps, Release Manager.

Überblick & Prinzipien
- Backend zuerst: API‑Contracts, Datenintegrität, Performance, Jobs/Asynchronität, und Money‑Precision. Gründe: verhindert inkonsistente DB‑Zustände und minimiert mehrfaches Refactoring in Frontend.
- Frontend danach: Anpassung an stabilisierte Contracts, Adapter/Normalizer statt fragile Änderungen überall im UI.
- Nicht-invasive Reihenfolge: wenn möglich, Einführung von kompatiblen Shims/Adapters, dann schrittweise harte Umstellung.

Prioritätsebenen (P0, P1, P2)
- P0 (Critical, must do before deploys): Stabilität, precision, contracts, large-op async pattern.
- P1 (High): UX/Performance improvements and shared abstractions in frontend to reduce duplication.
- P2 (Medium): Nice-to-have refactors, tests, docs, CI improvements.

1) Gesamtablauf (Sequencing)
- Phase A — Backend Stabilisierung (P0 → P1)
  1.1 Money precision & schemas (P0)
    - Ziel: Alle Geldfelder in DB/ORM/Schemas als Decimal/NUMERIC; Pydantic schemas benutzen `Decimal` oder stringified decimal; API gibt Beträge deterministisch (z.B. strings "123.45" oder integer cents).
    - Aufgaben:
      - DB‑Schema audit & migrations checklist (find all money columns in `models/` and migrations). Add `ALTER TABLE` migrations if needed.
      - Update Pydantic serializers + global JSON encoder to render Decimal as string.
      - Add unit tests for serialization/roundtrip at schema layer.
    - Risiko/Kommentar: Breaking change if frontend expects floats; plan must include backward-compatible API (return string and support numeric parsing in frontend shim).

  1.2 Endpoint response shape normalization (P0)
    - Ziel: Standardize list endpoints to `{ items: [...], total: N, page?: n, page_size?: m }` and errors to `{ error: { status, code, message, details? } }`.
    - Aufgaben:
      - Add schema docs and Pydantic response models for frequently-used endpoints (transactions, transfers, imports, categories, budgets).
      - Update routers to return canonical response models or add an adapter layer in routers.
    - Risiko: Minimal if adapters are used; ensure tests cover both old and new shapes during transition.

  1.3 Large operations → job system (P0)
    - Ziel: All heavy/long running ops (CSV import, recategorize, transfer detection, recurring detection, large deletes) must support job-based execution.
    - Contract: POST => either synchronous small-result OR `{ job_id }`. Job status read via `GET /jobs/{job_id}`; results accessible via `/jobs/{job_id}/result` or existing history endpoints (`/import-history/{id}`).
    - Aufgaben:
      - Implement reliable job table / job_service integration (if not already): enqueue, status update, result storage, error logs.
      - Update router endpoints to return `{ job_id }` for long ops; for small ops keep existing synchronous behavior.
      - Add idempotency/locking where required (e.g., import dedupe unique constraints).
    - Testing: Integration tests to simulate large import returning `{ job_id }` and poll to final state.

  1.4 Data processing & performance hardening (P0→P1)
    - Ziel: Replace full-table & in‑Python scans where possible with DB aggregations; streaming CSV parsing.
    - Aufgaben:
      - Replace full `.all()` loads in matchers with indexed candidate queries; add trigram/fulltext indexes for recipient matching when using Postgres.
      - Change CSV parsing to chunked streaming (pandas chunksize or csv.DictReader streaming) and set server-side file size limit.
      - Add DB indexes recommended in service audits (transaction_date, category_id, account_id, recipient normalized fields).

  1.5 Data integrity & constraints (P0)
    - Ziel: Add unique constraints where meaningful (e.g., `(account_id, file_hash)` in import_history), and foreign key cascade behaviors reviewed.
    - Aufgaben:
      - Create DB migrations for unique constraints and indexes.
      - Audit cascade deletes and consider async delete jobs for accounts with large datasets.

  1.6 Job & timestamp consistency (P1)
    - Ziel: Use timezone-aware timestamps across services and standardize SQLAlchemy usage (session.get vs deprecated .get()).

  Deliverables Phase A:
  - `audit/00_backend_action_plan.md` updated with explicit migration steps.
  - Migration PRs + tests for Decimal & constraints.
  - Job table + sample worker or local job-runner script and API contract docs.

- Phase B — Backend Contract Freeze & Docs (P0)
  2.1 API Contract Document (P0)
    - Ziel: A canonical `backend_api_contract.yaml` or `audit/backend_api_endpoints.md` listing critical endpoints, request/response examples, auth requirements, rate limits, and whether endpoint returns `job_id`.
    - Aufgaben:
      - Generate canonical list from `audit/06_backend_routers_endpoints.md` and expand with example bodies for CSV import, import-history, recategorize, transfers.
      - Publish in repo `/docs/api_contracts.md` and link from `/audit/`.

  2.2 Stability testing (P0)
    - Ziel: Add integration tests for critical endpoints (import preview, import start -> job flow, transactions list, transfers detect).
    - Aufgaben:
      - Add pytest integration tests exercising job polling.
      - Add tests for money serialization roundtrip.

- Phase C — Frontend adaptation & shims (start once Phase B docs stabilized)
  3.1 API Normalizer & Money Helpers (P0)
    - Ziel: Frontend implements small, centralized shims to accept old and new backend shapes with no user-visible regressions.
    - Tasks:
      - `frontend/src/services/api.js`: axios interceptors that normalize list responses into `{ items, total }`, normalize error shapes, coerce money fields via `parseAmount`.
      - `frontend/src/utils/amount.js`: `parseAmount(value)` and `formatAmount(value, opts)`; support numeric, string decimal, and cents.
      - Add unit tests for helpers.
    - Effort: small (0.5–1d).

  3.2 Job Poller & UX for long ops (P0)
    - Ziel: `jobPoller` helper and `ImportProgress` modal to handle `{ job_id }` responses gracefully.
    - Tasks:
      - Implement `frontend/src/services/jobPoller.js` with configurable backoff and cancellation.
      - Update `CsvImportWizard.jsx`, `CategoryMappingEditor.jsx`, `TransferManagementPage.jsx` to accept either synchronous result or `{ job_id }` and open `ImportProgress` or `JobProgress` modal.
    - Effort: medium (1–2d).

  3.3 Central hooks & pagination (P1)
    - Ziel: create `usePaginated` and `useFetchList` hooks to remove duplicate pagination code.
    - Tasks:
      - Implement hooks, migrate a few components (transactions table, transfers list) as proof-of-concept.
    - Effort: medium (2–3d).

  3.4 Chart utilities & data sampling (P1)
    - Goal: Add `chart-utils.js` to standardize formatting and sampling parameters; update `DataChart.jsx` and `RecipientPieChart.jsx` to use it.

  Deliverables Phase C:
  - `frontend` shim PRs with tests, UI change small and backwards-compatible.

2) Cross‑cutting non-functional tasks
- CI / Release
  - Add CI jobs for lint/test/build. Gate merging of changes to API contracts with updated frontend adapters.
- Migrations & Rollback plan
  - Every DB migration must include rollback notes and a small script to re-run for local dev.
- Monitoring & Alerts
  - Add metrics for job queue length, job failures, import processing durations, common 5xx spikes.

3) PR checklist & QA steps (for each PR)
- Small, single-purpose PRs.
- Unit tests added for new helpers / schema code.
- Integration tests for job flows and money serialization edge cases.
- Document contract changes in `docs/api_contracts.md`.
- Manual QA steps for UI changes: smoke test common user flows (CSV import small file, transactions list, create transfer).

4) Rollout & Feature flags
- Prefer feature-flagged rollout for breaking changes (e.g., switch frontend to expect `items` instead of `data` behind a flag).
- Deploy backend with backward-compatible adapters for 1–2 releases; after client adoption, remove legacy adapters.

5) Time estimates (rough)
- Backend P0 (money precision, job system, endpoint normalization): 5–10 dev days (split across 2–3 PRs).
- Backend P1 (performance indexing, streaming): 3–6 dev days.
- Frontend P0 (api-normalizer, jobPoller, amount helpers): 2–4 dev days.
- Frontend P1 (hooks, chart-utils): 3–6 dev days.

6) Quick wins (first 48h)
- Add `audit/00_total_action_plan.md` (this file).
- Implement frontend `parseAmount` + minimal api interceptor shim (0.5–1d).
- Add server config for max file size on CSV uploads (small infrastructure change).

7) Risks & mitigations
- Risk: Backend schema change (Decimal) may break existing clients. Mitigation: return string decimals and keep backward-compatible parsing on client.
- Risk: Job system complexity. Mitigation: start with synchronous small-sample mode, add `{ job_id }` for large runs; provide stable job table and simple worker runner for initial rollout.

8) Communication & coordination
- Create a short RFC PR describing contract changes and annotate `/audit/backend_api_endpoints.md` with expected timeline.
- Schedule a 30‑minute sync between backend & frontend maintainers to confirm on-contract details (CSV import, amount format, jobs behaviour).

9) Next immediate actions I will take if du mir das erlaubst
- Option A (recommended immediate): Implement frontend `parseAmount` helper + axios interceptor shim and run unit tests. This is low-risk and prevents UI breakage during backend migrations.
- Option B: Produce `docs/api_contracts.md` from `audit/06_backend_routers_endpoints.md`, highlighting endpoints that will change (CSV import, recategorize, transfers). Useful for coordination.
- Option C: Start backend migrations branch scaffold to convert money columns to Decimal (requires DB access and careful planning) — requires your approval.

---

Referenzen
- bestehende Audit‑MDs: `audit/00_backend_action_plan.md`, `audit/05_backend_services.md`, `audit/06_backend_routers_endpoints.md`, `audit/12_frontend_components.md`, `audit/13_frontend_components.md`.

```