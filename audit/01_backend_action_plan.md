**TL;DR**
- Centralized, prioritized action plan for the backend based on the per-folder audits (`01`..`07`).
- Goals: remove duplication, centralize reusable logic into services/utils, ensure data correctness (Decimals, DB constraints & migrations), make heavy work backgroundable, and improve performance and portability.

Purpose
- Provide a small set of concrete, prioritized tasks (with file-level pointers) to implement across the backend. Each task is framed so it can be completed independently (small PRs) while keeping duplication low by adding shared utilities or services.

Priority Legend
- P0 = Immediate (fixes that reduce clear correctness or safety risks)
- P1 = High (important for reliability, performance or consistency)
- P2 = Medium (quality, maintainability, extensibility)
- P3 = Low (nice-to-have, documentation, small refactors)

P0 — Correctness & Safety (apply first)
- Replace floats with Decimal (end-to-end):
  - Files: `services/csv_processor.py`, `services/transfer_matcher.py`, `services/data_aggregator.py`, `schemas/*`, `models/*` where money present.
  - Action: add `app/utils/money.py` with helpers: `to_decimal(value)`, `quantize_amount(d)`, and JSON encoder helper for Decimal. Update Pydantic `model_config` to use Decimal encoder.
  - Reason: prevents accounting precision bugs.

- Enforce import dedupe at DB level:
  - Files: `migrations/006_add_import_history.sql` (add unique index), `services/import_history_service.py`.
  - Action: add migration to create unique index on `(account_id, file_hash)` and update `create_import_record` to handle IntegrityError (return existing record or fail gracefully).
  - Reason: prevents race-condition duplicate imports.

- Limit / stream CSV imports and make import pipeline resilient:
  - Files: `routers/csv_import.py`, `services/csv_processor.py`, `services/import_history_service.py`.
  - Action: add `settings.MAX_IMPORT_ROWS`, `settings.MAX_IMPORT_BYTES`; implement streaming parsing (chunks) in `CsvProcessor` and accept large files only via background job (enqueue import job and return job id). Keep a lightweight preview endpoint that still reads limited rows.
  - Reason: Prevent OOM/DoS and long synchronous requests.

P1 — Performance, Portability & Data Integrity
- Centralize decimal / money rules and hashing normalization:
  - Files: `services/hash_service.py`, `services/transfer_matcher.py`, `services/recurring_transaction_detector.py`.
  - Action: Use `app/utils/money.py` to format Decimal consistently before hashing or matching; update `HashService.generate_hash` to normalize dates/amounts consistently.

- Move heavy detections & aggregations to background jobs + `JobService`:
  - Files: `routers/csv_import.py`, `services/recurring_transaction_detector.py`, `services/insights_generator.py`, `services/job_service.py`.
  - Action: For imports that exceed small thresholds, create an import job (persist job record) and run full processing in background worker (FastAPI `BackgroundTasks` or external worker). Return job id for frontend polling via `import_history` endpoints.

- Create DB-agnostic aggregation helpers:
  - Files: `services/data_aggregator.py`, `utils/db_utils.py`.
  - Action: Implement a small dialect mapping (e.g., `group_date(db_engine, column, period)`) to avoid `strftime`/`date_trunc` branching throughout code. Use SQLAlchemy constructs where possible.

- Normalize recipient aliases & improve fuzzy search:
  - Files: `models/recipient.py`, `migrations/` (new), `services/recipient_matcher.py`.
  - Action: Introduce `recipient_aliases` table with `recipient_id, alias`. Migrate existing comma-separated aliases to rows via migration script. Replace CSV-based alias lookups with joins and optionally add trigram index (Postgres) behind a feature flag.

- Avoid N+1 queries: eager-loading helpers
  - Files: `routers/transfers.py`, `routers/recurring.py`, `services/*` that load relations.
  - Action: Create `app/utils/orm.py` with `eager_load_relations(query, *rels)` helpers and use `joinedload/selectinload` where routers require details.

P2 — Design & Maintainability
- Centralize pagination & safe-count logic:
  - Files: `utils/pagination.py`, routers using `paginate_query`.
  - Action: Add `db_utils.safe_count(query, db_session)` that builds efficient count queries and remove `.all()` fallback. Add cursor pagination helper for large tables.

- Make logging initialization explicit and support request context:
  - Files: `utils/logger.py`, `main.py`.
  - Action: Change `logger.py` to expose `init_logging(level=None, pretty=None, force=False)` and remove auto-call on import. Add `RequestContextFilter` to attach `request_id` from a `contextvar` middleware.

- Consolidate matching/normalization logic into small utilities:
  - Files: `utils/text_utils.py`, `services/category_matcher.py`, `services/recipient_matcher.py`.
  - Action: Add `normalize_text(s)`, `tokenize`, `approx_similarity(a,b)` helpers used by matchers to avoid duplicated normalization/cleanup.

- Add explicit `ServiceError` classes and central HTTP mapping:
  - Files: `services/errors.py`, `main.py` exception handlers.
  - Action: Raise `ServiceError`/`NotFoundError`/`ValidationError` in services and map to HTTP in `main.py` with structured `ErrorResponse`.

P3 — Cleanups & Nice-to-haves
- Schema consistency & Pydantic v2 config
  - Files: `schemas/*`.
  - Action: Standardize `model_config = ConfigDict(from_attributes=True)` and ensure `Decimal` encoding is configured globally.

- Add explicit DB CHECK constraints where missing (mirror validators):
  - Files: `models/budget.py`, `models/recurring_transaction.py`, `models/transfer.py`.
  - Action: Add `CheckConstraint` lines and corresponding unit tests to guarantee invariants.

- Tests & CI
  - Add test cases for CSV import edge cases, transfer detection with Decimal tolerance, recipient merging, and service-level unit tests.

How to avoid duplication (design rules)
- Prefer small focused utilities/services over repeated logic in routers/services:
  - `app/utils/money.py` — Decimal conversion, quantize rules, JSON encoder.
  - `app/utils/csv_stream.py` — streaming CSV parsing with normalization hooks.
  - `app/utils/db_utils.py` — safe_count, dialect helpers, transaction helpers.
  - `app/utils/text_utils.py` — normalization, tokenization, similarity.
  - `app/services/matcher_base.py` — small base class for matchers (category/recipient/transfer) with shared methods for caching, normalization and bulk-match API.

Suggested PR breakdown (small, reviewable units)
- PR 1 (P0): Add `app/utils/money.py`, update `CsvProcessor` to return Decimal values for amounts, and update a couple of schemas to accept Decimal. Add tests.
- PR 2 (P0): Add unique index migration for `(account_id, file_hash)` and handle IntegrityError in `ImportHistoryService.create_import_record`.
- PR 3 (P0/P1): Implement streaming CSV parsing and API changes to enqueue large imports via `JobService` (update `csv_import` router to return job id). Add `MAX_IMPORT_ROWS`+`MAX_IMPORT_BYTES` settings.
- PR 4 (P1): Normalize recipient aliases: migration + `recipient_aliases` model + update `RecipientMatcher` to use alias table.
- PR 5 (P1): Add `db_utils.safe_count` and update `pagination.paginate_query` to use it; remove `.all()` fallback.
- PR 6 (P1/P2): Replace `logger._configure_root()` auto-init with `init_logging()` and add `RequestContextFilter` and small middleware to set request_id.
- PR 7 (P2): Centralize matching helpers and refactor `CategoryMatcher`/`RecipientMatcher` to use them.

Acceptance criteria for each PR
- Small focused tests covering functionality and edge cases (decimal math, large file handling, unique import behavior).
- Migration tested locally (SQLite) and reviewed for Postgres compatibility (if target).
- No duplication introduced; utilities used by at least two callers to justify centralization.

Appendix: high-level mapping of shared utilities vs owners
- `app/utils/money.py` — owner: services team (used by CsvProcessor, HashService, TransferMatcher, Aggregators)
- `app/utils/csv_stream.py` — owner: import team (routers/csv_import and CsvProcessor)
- `app/utils/db_utils.py` — owner: platform (used by pagination, services needing safe_count, job service)
- `app/utils/text_utils.py` — owner: matching team (CategoryMatcher, RecipientMatcher, MappingSuggester)