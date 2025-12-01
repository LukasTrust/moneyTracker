**TL;DR**
- **Scope**: File-by-file audit of `backend/app/routers` (FastAPI endpoints).
- **High-level**: Routers are well-structured and follow a router-per-resource pattern. Major risks center on CSV import memory/validation, numeric precision (float vs Decimal), large synchronous DB operations, and repeated full-table scans for matching/search. Immediate priorities: harden `csv_import`, adopt Decimal consistently, and add server-side limits / streaming for heavy operations.

**Integration note**: Refer to `01_backend_overview.md` → "Interplay / System Map" for the canonical mapping between routers, services, models, schemas, and migrations. When applying router-level fixes, update the matching service and schema files to keep API contracts and DB migrations in sync (e.g., `csv_import` → `CsvProcessor`/`ImportHistoryService`, `recurring` endpoints → `recurring_transaction_detector`, `transfers` → `transfer_matcher`).

**Per-Router Analysis**

**`accounts.py`**
- **Purpose**: CRUD for `Account` and safe deletion including cleanup of recurring transactions.
- **What I found**: Good defensive code for direct-test invocation compatibility. Uses `text()` raw SQL to delete recurring links to avoid ORM-side integrity issues.
- **Risks / Issues**:
  - Direct SQL deletion is acceptable but should be documented and tested across DB backends (behaviour may differ between SQLite/Postgres/MySQL).
  - No soft-delete option or audit trail — deletes are irreversible.
- **Suggestions**:
  - Wrap raw SQL in a helper (`app.services.cleanup`) and add DB-specific tests.
  - Consider returning more informative responses for delete (e.g., deleted counts) or adding soft-delete if needed.
- **Risk**: Low → Medium (depends on DB portability requirements).

**`categories.py`**
- **Purpose**: Manage categories and mapping patterns; recategorization endpoint.
- **What I found**: Patterns stored in a JSON `mappings` field with `attributes.flag_modified` used correctly when mutated. Bulk recategorization performs batched updates and uses `CategoryMatcher`.
- **Risks / Issues**:
  - Mutable JSON in DB — good that `flag_modified` is used, but storing many patterns in a single JSON blob can complicate queries and scaling.
  - `recategorize` iterates many rows; it's implemented in batches but may still be heavy for very large datasets.
- **Suggestions**:
  - Normalize patterns into a separate table (`category_patterns`) for indexing and faster conflict checks.
  - Add an explicit max rows limit, throttling, or a background job for `recategorize` for very large accounts.
- **Example (pattern normalization)**:
  - Before (current): `Category.mappings = {'patterns': [...]}`
  - After (suggestion): add `CategoryPattern` table with `(category_id, pattern, created_at)` and index on `lower(pattern)`.
- **Risk**: Medium.

**`csv_import.py`** (highest priority)
- **Purpose**: Advanced CSV import pipeline (preview, detect bank, mapping suggestions, import flow).
- **What I found**: The endpoint performs the full import synchronously within the request for many operations (parsing with Pandas, per-row validation, matching, insert), but does attempt to use `BackgroundTasks` for post-import detection. It writes import history, calculates hashes, persists `DataRow` rows, triggers recurring detection and transfer detection, and saves mappings.
- **Major Risks**:
  - **Memory & DoS**: `CsvProcessor.parse_csv_advanced` returns a DataFrame loaded fully into memory. A large CSV can cause OOM. No file size or row limits are enforced at the API layer.
  - **Precision**: Amounts are parsed/validated as floats — risk of rounding errors and accounting bugs.
  - **Synchronous heavy work**: The main endpoint performs many DB operations and CPU work inline. This blocks worker processes and increases latency.
  - **Duplicate detection retrieval**: `existing_hashes` loads row hashes for the entire account into a set — large accounts could make this large.
- **Suggestions (priority list)**:
  1. Enforce max file size + row count in API and UI; reject or require background import for large files.
  2. Stream parsing: replace full DataFrame with an iterator / streaming parser (e.g., `pandas.read_csv(..., chunksize=...)` or `csv` + streaming) and process in batches.
  3. Persist amounts using `Decimal` (DB `Numeric`) and validate using Decimal in Pydantic. Update `CsvProcessor` and `TransactionRow` schema to return Decimal.
  4. Move heavy detectors (recurring, transfer) to background jobs and only return job IDs to frontend; keep a synchronous lightweight import when possible.
  5. Replace `existing_hashes` set loading with a DB uniqueness constraint on `(account_id, row_hash)` + upsert/ignore semantics or check via single-row query before insert.
  6. Limit the size of `raw_data` stored or compress it; optionally store raw CSV in blob storage instead of row-by-row JSON if needed.
- **Code example (streaming pseudocode)**:
  - Before: `df = CsvProcessor.parse_csv_advanced(content); for row in mapped_data: ... db.add(DataRow(...))`
  - After: use chunk iterator and `bulk_insert_mappings` or batched `INSERT` with SQLAlchemy Core; validate each chunk and commit in controlled sizes.
- **Risk**: High — immediate production impact.

**`import_history.py`**
- **Purpose**: List imports, details, rollback, delete import metadata.
- **What I found**: `get_import_details` uses the service that returns multiple imports and filters in Python (inefficient). Rollback delegates to `ImportHistoryService.rollback_import` (good separation).
- **Suggestions**:
  - Add query-level filtering in `ImportHistoryService.get_import_history_with_stats` to fetch a single import directly.
  - Ensure `rollback_import` is covered by tests and transactional (atomic) deletion.
- **Risk**: Medium (rollback is risky operation but looks encapsulated).

**`recurring.py`**
- **Purpose**: Manage recurring transaction detection and manual overrides.
- **What I found**: Good use of `BackgroundTasks` and `JobService` to enqueue heavy detection jobs. Several endpoints compute monthly costs using `float()` casts.
- **Risks / Suggestions**:
  - Replace float math with Decimal for `average_amount` and monthly computations.
  - Ensure `run_update_recurring_transactions_all` is idempotent and safe to retry; add job locking to avoid duplicate concurrent runs.
- **Risk**: Medium.

**`recipients.py`**
- **Purpose**: CRUD for recipients, merging, suggestions.
- **What I found**: Aliases stored as comma-separated strings (`aliases` column). `get_recipients` filters using `ilike` across `aliases` field, which is a text field; `get_merge_suggestions` uses `RecipientMatcher` service.
- **Risks / Suggestions**:
  - Normalize aliases into a separate `recipient_aliases` table to allow indexing and trigram search.
  - Avoid storing list defaults as `[]` in Pydantic schema definitions (in-router schemas use default mutable list) — move to `None` or `field(default_factory=list)` in real models.
  - Add rate limits if merge operations can be expensive.
- **Risk**: Medium.

**`mappings.py`**
- **Purpose**: Manage CSV header mappings for accounts.
- **What I found**: Replaces mappings wholesale per account (DELETE + INSERT). That's simple and acceptable.
- **Suggestion**:
  - Wrap deletion+creation in a transaction (currently all in one commit — OK, but ensure no partial writes on exceptions).
- **Risk**: Low.

**`data.py`**
- **Purpose**: Transaction retrieval, summaries, statistics via `DataAggregator` service.
- **What I found**: Filters support many combinations; uses `ilike` for searches and calls into `DataAggregator` for heavy aggregations (good separation). Pagination and server-side limits are applied.
- **Risks / Suggestions**:
  - Amount filters use floats — migrate to Decimal.
  - Ensure `DataAggregator` pushes down filters into SQL (it should) to avoid in-memory aggregation.
  - Add index recommendations: `transaction_date`, `category_id`, and `recipient` (GIN/trigram) for better performance on searches.
- **Risk**: Medium.

**`transfers.py`**
- **Purpose**: CRUD and detection of transfers, plus stats.
- **What I found**: Good candidate detection via `TransferMatcher`. When `include_details=True`, the router loads related `DataRow` and `Account` rows per transfer in a loop (N+1 queries). It also converts amounts via `float()` for response.
- **Suggestions**:
  - Use joined eager loading (`join`/`options(joinedload(...))`) to avoid N+1 when fetching details.
  - Return Decimal-encoded amounts (Pydantic config) instead of casting to float.
  - Add DB constraint/unique index to prevent duplicate transfers (unique on `(from_transaction_id, to_transaction_id)` where appropriate).
- **Risk**: Medium.

**`budgets.py`, `comparison.py`, `dashboard.py`, `insights.py`** (grouped)
- **Purpose**: Analytics endpoints and budget management.
- **What I found**: Good separation of concerns; heavy work delegated to `BudgetTracker`, `DataAggregator`, `InsightsGenerator` services. Some numeric math uses floats.
- **Suggestions**:
  - Migrate amount math to Decimal across services.
  - Ensure long-running generation (`insights.generate`) is rate-limited or enqueued as background job when doing full-analysis.
- **Risk**: Medium.

**`deps.py`**
- **Purpose**: Provides `get_account_by_id` and `verify_account_exists` helpers.
- **What I found**: Clean and reusable. Consider centralizing other common deps here if needed.
- **Risk**: Low.

**Cross-Cutting Concerns & Recommendations**
- **Monetary Precision (High priority)**: Replace float usage across routers/services with `Decimal`. Update Pydantic schemas and set JSON encoders (e.g., `jsonable_encoder` or Pydantic `Config`) to serialize Decimal to string.
- **CSV import scaling (High priority)**: Enforce limits; stream parse; move heavy detectors to background jobs; prevent full-account `existing_hashes` set loading — use DB constraints/upserts.
- **Background jobs & idempotency (Medium priority)**: Use `JobService` consistently for long tasks and implement job locking (advisable using DB row-lock or Redis distributed lock) to prevent duplicate concurrent runs.
- **Search performance (Medium priority)**: Add trigram/GIN indexes or full-text indexes for `recipient` and `purpose` if fuzzy search is required. Consider `pg_trgm` for Postgres.
- **N+1 queries (Medium)**: Use `joinedload`/`selectinload` or explicit joins where joined data is needed (e.g., transfer details, recurring category names).

**Suggested Quick Wins (order by impact)**
- Add server-side `MAX_FILE_ROWS` and `MAX_FILE_BYTES` settings and enforce them in `csv_import` endpoints.
- Add DB unique constraint `(account_id, row_hash)` and use INSERT ON CONFLICT DO NOTHING (or equivalent) to deduplicate efficiently.
- Convert amounts to Decimal end-to-end (CSV parser → Pydantic → DB) and provide API-friendly serialization.
- Offload `recategorize` and `import`-phase detectors to background jobs with progress/status via `JobService`.

**Next Steps**
- I will produce the `routers` audit file (this file) and stop as requested. Confirm if you want me to:
  - Implement the quick wins in code (patches), or
  - Continue with the frontend audit next.

**Summary Rating**
- Overall: healthy codebase with real-world pragmatism; main technical debt: CSV import/workflow scaling and numeric precision. Addressing those will substantially raise reliability and production safety.
