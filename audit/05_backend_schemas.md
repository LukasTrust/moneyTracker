- Ich habe die Migrations-SQLs `004_add_budgets.sql` .. `008_add_insights.sql` gelesen und folgende wichtige Punkte extrahiert, die Ihr Schema- und Model-Layer sowie die Pydantic-Schemas betreffen:

- `004_add_budgets.sql` (Budgets)
  - DB-Typen: `amount NUMERIC(12,2)` — bestätigt, dass `Budget.amount` sollte `Decimal`/`Numeric` sein in Models/Schemas.
  - DB-Constraints: `CHECK (amount > 0)` und `CHECK (end_date >= start_date)` — diese Regeln fehlen teilweise nur als runtime-validierung in Pydantic; ergänzen Sie dieselben Prüfungen in `budget`-Schemas (Pydantic validators) und idealerweise passende DB-constraints in SQLAlchemy metadata (if not already present).
  - Indizes: mehrere Indizes auf `category_id`, `start_date`, `end_date` — empfehlen, die Modelle zu dokumentieren und bei Performance-Trouble die Indizes zu spiegeln.
  - Trigger: `updated_at`-Trigger — ORM-Modelle nutzen momentan `server_default`/Python-side timestamps; prüfen ob beibehalten oder DB-trigger bevorzugt wird.

- `005_add_recurring_transactions.sql` (Recurring transactions)
  - Viele Felder nutzen `NUMERIC(12,2)` für money (`average_amount`) and `INTEGER` for counts — Pydantic schemas must use `Decimal` for amounts and `int` for counts.
  - Important CHECK constraints: `occurrence_count >= 3`, `average_interval_days > 0`, `last_occurrence >= first_occurrence`, `confidence_score` range — migrate these validations into Pydantic validators where business logic requires user-facing errors; keep DB CHECKs as last-line enforcement.
  - `recurring_transaction_links` junction table exists — schemas that expose linked rows should document this relation and possibly include `recurring_links` in response models.

- `006_add_import_history.sql` (Import history)
  - New `import_history` table with `file_hash` and stats fields and an added `import_id` column on `data_rows`.
  - Important: there is no DB-unique constraint on `(account_id, file_hash)` in migration — earlier audit recommended enforcing uniqueness to avoid duplicate imports; consider adding a unique index to prevent accidental double-imports.
  - Because `data_rows.import_id` is nullable and indexed, update `DataRow` schema and Pydantic models to include `import_id` (and ensure `ImportHistory` response schemas include `file_hash`, `status`, `rows_inserted` etc.).

- `007_add_transfers.sql` (Transfers)
  - `amount DECIMAL(12,2)` and `confidence_score DECIMAL(3,2)` — use `Decimal` in schemas.
  - Unique index to prevent duplicate transfer links uses `MIN()/MAX()` in the SQL index expression — this is a clever SQLite-specific trick; it's not portable to all RDBMS or ORM-level unique constraints. Recommendation: implement canonical ordering in application logic (ensure from_id < to_id when storing) and add a plain unique constraint on `(from_transaction_id, to_transaction_id)` (or `(min_id, max_id)` persisted columns) to ensure portability.
  - Migration inserts a `Transfer` category row in `categories` — frontends/schemas expecting this category should be tolerant if missing.

- `008_add_insights.sql` (Insights + logs)
  - `insight_data` and `generation_params` stored as `JSON` — Pydantic `insight_data: Optional[dict]` is OK, but recommend adding JSON-shape validators for common insight types to avoid brittle frontend contracts.
  - Partial index in migration (`WHERE is_dismissed = 0`) is Postgres-style; if you run on SQLite the partial index syntax may be ignored — align migrations to the target DB or provide DB-specific migrations.
  - Timestamps and cooldown tracking exist in DB — ensure schemas expose `last_shown_at`, `show_count`, `cooldown_hours`, `valid_until` consistently.

H. Konkrete Anpassungsaufgaben für `schemas` (Priorisiert)
- 1) Ensure all monetary fields in Pydantic schemas use `Decimal` and `model_config` / JSON encoders serialize Decimal safely (string preferred for OpenAPI/JSON).
- 2) Add validators mirroring DB CHECK constraints for immediate user feedback (budgets: `amount>0`, `end_date>=start_date`; recurring: `occurrence_count>=3`, etc.).
- 3) Add `import_id` to `DataRow` schemas and `ImportHistory` fields (`file_hash`, `status`, `rows_inserted`) to response models.
- 4) Update transfer-related schemas to document canonical ordering and include `confidence_score` typed as Decimal.
- 5) For `insight_data` and `generation_params`, add optional typed variants or JSONSchema examples for common shapes; keep a permissive fallback `dict`.
- 6) Document DB/ORM differences for partial indexes and migration portability (SQLite vs Postgres). If production target is Postgres, add Postgres-specific migration notes (GIN/JSONB, partial indexes, pg_trgm for text search).

I. Small migration vs model diffs I noted (actionable)
- `data_rows` now contains `import_id` — some older code paths may assume this column doesn't exist; ensure all DataRow-related code handles `import_id` being present/nullable.
- No `(account_id,file_hash)` unique constraint exists — consider adding migration to enforce it and updating `ImportHistoryService.create_import_record` to upsert or to check for duplicates via DB constraint.
- Transfer uniqueness using `MIN/MAX(...)` index expression is not portable; propose adding application-level canonicalization and a simple unique index on `(from_transaction_id, to_transaction_id)` after canonicalization.

**Integration note**: See `01_backend_overview.md` → "Interplay / System Map" for the canonical mapping between schemas and DB models/migrations. Important crosschecks you should make when changing schemas:
- Ensure Pydantic money fields (`Decimal`) align with DB `NUMERIC/DECIMAL` columns in migrations (`budgets.amount`, `recurring.average_amount`, `transfers.amount`).
- Add validators that mirror DB `CHECK` constraints for immediate client-side feedback (budgets, recurring, transfers).
- When adding `import_id` to `DataRow` schemas, confirm `migrations/006_add_import_history.sql` already adds the column and index.

J. Abschluss
- Ich habe die Migrations geprüft und den `schemas`-Audit erweitert. Soll ich jetzt (A) implementieren die Pydantic schema-Änderungen (patch: `schemas` -> Decimal + validators + `import_id`), oder (B) weiter zum nächsten Ordner (`services`/frontend)?
  - Observations:
    - `TransactionRow` accepts `date: str` with comment that parsing happens in import logic — this is pragmatic but can push parsing errors later; consider `StrictStr` or an explicit `date` validator to provide better OpenAPI docs.
    - `CsvImportMapping` and `FieldMapping` include validators ensuring only allowed fields are used — good.
    - `CsvImportResponse` provides a rich response and example — good for client integration.

- `data_row.py`
  - Purpose: API representation for DataRow.
  - Observation: `data: Dict[str, Any]` used to preserve flexible legacy fields. Prefer explicit typed schema where possible (date, amount, recipient, purpose) and fallback `raw_data` for extras.

- `import_history.py`
  - Purpose: Import history API models and rollback request/response.
  - Observations: `model_config = ConfigDict(from_attributes=True)` used appropriately in some responses (Pydantic v2). `status` pattern provided. `ImportHistoryStats` returns Decimal fields — good.

- `insight.py`
  - Purpose: Insight CRUD and generation endpoints.
  - Observations: `insight_data: Optional[Dict[str, Any]]` is flexible but unvalidated; consider JSON Schema or TypedUnion for common insight shapes to avoid front-end surprises.

- `mapping.py`
  - Purpose: Mapping CRUD — straightforward.

- `recurring_transaction.py` & `transfer.py` & `statistics.py`
  - Purpose: Schemas for recurring transactions, transfers, and aggregated statistics.
  - Observations:
    - `field_validator` usage in `transfer` and `recurring` to enforce IDs and occurrence counts — good.
    - `TransferCandidate` includes nested dicts for transactions; consider typed `DataRowResponse` references for clearer contracts.

**C. Codebeispiele (vorher / nachher)**
1) Inconsistent Pydantic v2 config usage

Vorher (`account.py`):
```py
class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

Nachher (einheitlich, Pydantic v2):
```py
from pydantic import ConfigDict
class AccountResponse(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

2) `TransactionRow` Date Parsing

Vorher (`csv.py`):
```py
class TransactionRow(BaseModel):
    date: str
    amount: float
    recipient: str
    purpose: Optional[str]
```

Nachher (empfehlung):
```py
from datetime import date
from pydantic import field_validator
class TransactionRow(BaseModel):
    date: date
    amount: Decimal
    recipient: str
    purpose: Optional[str]

    @field_validator('date', mode='before')
    def parse_date(cls, v):
        # accept string and parse to date or validate date objects
        return parse_some_date_logic(v)
```

**D. Konkrete Refactoring-Vorschläge**
- Standardisiere auf Pydantic v2 `model_config = ConfigDict(from_attributes=True)` in allen response schemas.
- Use `Decimal` consistently for monetary fields in schemas that represent money (avoid `float`). Update endpoints to return Decimal-serializable formats (strings) or configure Pydantic JSON encoders.
- Tighten flexible `Dict[str, Any]` fields by adding optional typed variants or JSON Schema validators for common shapes (e.g., `insight_data`, `data` inside `DataRowResponse`).
- For CSV parsing, optionally move parsing to a pre-validation step that uses Pydantic validators so errors surface in API responses with clear messages.

**E. Risikobewertung**
- Inconsistent use of Decimal vs float for monetary fields: Medium (precision/rounding issues).
- Flexible JSON fields without schema (`insight_data`, `data`): Low→Medium (frontend/backward compatibility issues).
- Mixed Pydantic config styles: Low (cosmetic but affects consistency and onboarding).

**F. Ungelöste TODOs / Hinweise**
- Ensure OpenAPI generation shows correct examples and types (Decimal rendering in OpenAPI might need custom encoders).
- Add tests for schema validation especially for boundary cases (budget dates, transfer ids, CSV mapping edge cases).

---
Ich habe das `schemas`-Verzeichnis vollständig analysiert und `/audit/04_backend_schemas.md` erstellt. Soll ich mit dem nächsten Ordner `routers/` weitermachen? I stop here per-folder as requested.