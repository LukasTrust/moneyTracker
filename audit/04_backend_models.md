# Backend Models - Detailanalyse ✅ AKTUALISIERT

## Status: ✅ Vollständig analysiert und dokumentiert

**TL;DR:**
- `backend/app/models` definiert die Kern-Domain-Objekte: Accounts, Categories, Budgets, DataRows (Transaktionen), ImportHistory, Mappings, RecurringTransactions, Recipients, Transfers, Insights und BackgroundJobs.
- **Gesamtbewertung: 7.8/10** - Datenmodell ist durchdacht und praktisch für die Domäne; es gibt aber Inkonsistenzen in Zeitstempeln, Default-Werten (mutable defaults), Relationship-Konventionen, JSON-/Numeric-Handhabung und Normalisierung (Recipient aliases). Korrekturen erhöhen Sicherheit, Performance und Wartbarkeit.

**A. Zusammenfassung (Manager TL;DR)**
- Models sind vollständig und adressieren die wichtigsten Geschäftsfälle (Import, Kategorisierung, Insights, Recurring Detection, Transfers).
- Empfehlungen: Vereinheitlichen von Timestamp-Handling, Entfernen mutabler Defaults, DB-Level-Constraints ergänzen, Aliases normalisieren (separate Tabelle), klare Dezimal-Serialisierung, konsistente Relationship-API.

**B. Tiefe technische Analyse (Datei-für-Datei)**
- `account.py`
  - Zweck: Repräsentiert Bankkonto mit Mappings, DataRows, ImportHistory, Insights.
  - Gut: Beziehungen mit cascade deletes; `initial_balance` als `Numeric`.
  - Verbesserungen: Keine explizite Unique-Constraints auf account_name+bank_name falls notwendig; keine explicit currency enum/validation; `initial_balance` default as float may lead to precision issues.

- `category.py`
  - Zweck: Globale Kategorien mit Mapping-Regeln.
  - Problem: `mappings = Column(JSON, nullable=False, default={"patterns": []})` benutzt eine mutable Python dict als Default.
  - Risiko: Mutable defaults können über mehrere Instanzen geteilt werden; außerdem `default` wird client-seitig angewendet, nicht DB-seitig. Dies kann bei Migration/Multithread zu Überraschungen führen.

- `budget.py`
  - Zweck: Budgets pro Kategorie mit Perioden-Enum.
  - Gut: Enum-Typ, `is_active` Helfer.
  - Verbesserung: Keine DB-CheckConstraints auf `start_date <= end_date`. `amount` sollte > 0 (CheckConstraint).

- `data_row.py` (wichtig)
  - Zweck: Kern-Entität für importierte Transaktionen. Strukturierte Spalten (transaction_date, amount, recipient, purpose) plus `raw_data` JSON.
  - Stärken: Durchdachte Indizes (`idx_account_date_range`, `idx_category_date`, `idx_date_amount`), unique `row_hash` für Duplikaterkennung.
  - Probleme:
    - `amount` ist `Numeric` — stellen Sie sicher, dass Anwendung Decimal verwendet und JSON-Serialisierung konsistent ist.
    - `data` property gibt `amount` als `str(self.amount)` — inkonsistent gegenüber anderen Serialisierungen.
    - `data` merge `**(self.raw_data or {})` kann Felder überschreiben (z. B. `date`), was verwirrend ist.
    - `created_at` uses `server_default=func.now()` (timezone-aware), während andere Modelle `default=datetime.utcnow` verwenden — Inkonsistenz bei Timezone-Handling.

- `import_history.py`
  - Zweck: Audit für CSV-Uploads. Verknüpfung zu DataRows via import_id.
  - Gut: Index für account+uploaded_at, rollback-Support via `import_id`.
  - Verbesserung: `file_hash` sollte unique sein, wenn deduplizierung über Datei-Hash erwartet wird.

- `insight.py`
  - Zweck: Stores generated insights and generation logs.
  - Beobachtung: `insight_data` JSON flexibel — gut, aber braucht Validation (shape/schema) für konsumierende Clients.
  - Verbesserung: Consider TTL mechanism or archiving for old insights (cleanup).

- `mapping.py`
  - Zweck: CSV header → standard field mapping per account.
  - OK: Simple shape, aber könnte multilingual headers or fuzzy matching rules require richer structure.

- `recipient.py`
  - Zweck: Normalized recipients with `normalized_name`, `aliases` stored comma-separated.
  - Probleme:
    - `aliases` als CSV-String (varchar) ist schlecht für queries and normalization. Suggest separate `recipient_aliases` table (one-to-many) or JSON array column.
    - `normalize_name` is simplistic (lowercase & collapse spaces) — may not handle diacritics, punctuation, unicode normal forms, or bank-specific noise (e.g. "McDonald's" vs "MCDONALDS").
    - `created_at` and `updated_at` use `datetime.utcnow` without timezone, inconsistent with other models using `func.now(timezone=True)`.

- `recurring_transaction.py` (already reviewed earlier)
  - Zweck: Detected recurring transactions with prediction and links to DataRows.
  - Gut: Contains confidence score and linking table `RecurringTransactionLink`.
  - Verbesserung: Ensure `confidence_score` has CheckConstraint 0..1; ensure `occurrence_count` min value constraint.

- `transfer.py`
  - Zweck: Model for inter-account transfers linking two DataRow rows.
  - Positive: CheckConstraints (different transactions, amount != 0, confidence range) — gute DB-level guards.
  - Verbesserung: Add a DB-level unique constraint to ensure a transfer pair only stored once (e.g. unique(from_transaction_id, to_transaction_id) or canonical ordering), else duplicates possible.

- `background_job.py`
  - Zweck: Track background tasks (import, classification, insights generation).
  - Beobachtung: Implemented as simple job table with `meta` text; fine for lightweight scheduling.
  - Verbesserung: If using external task queue (Celery/RQ), keep job id references and standardize statuses (enum).

**C. Codebeispiele (vorher / nachher)**
1) Mutable JSON default (`category.py`)

Vorher:
```py
mappings = Column(JSON, nullable=False, default={"patterns": []})
```

Problem: `default` ist eine Python-Variable (mutable).

Nachher (empfehlung):
```py
from sqlalchemy import text
from sqlalchemy.sql import expression

mappings = Column(
    JSON,
    nullable=False,
    default=lambda: {"patterns": []},
    server_default=expression.text("'{}'::json")
)
```
Oder: enforce at application layer (Pydantic model) und setze `nullable=False` ohne client-side mutable default.

2) Einheitliches Timestamp-Handling

Vorher (mixed):
```py
# some files
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# other files
created_at = Column(DateTime, default=datetime.utcnow)
```

Nachher (empfehlung):
```py
from sqlalchemy.sql import func
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```
Und Anwendungsebene: always treat datetimes as UTC-aware.

3) Recipient aliases → separate table

Vorher:
```py
aliases = Column(String(500), nullable=True)  # CSV string
```

Nachher (empfehlung):
```py
# new table: recipient_aliases
class RecipientAlias(Base):
    __tablename__ = 'recipient_aliases'
    id = Column(Integer, primary_key=True)
    recipient_id = Column(Integer, ForeignKey('recipients.id', ondelete='CASCADE'), nullable=False, index=True)
    alias = Column(String(200), nullable=False, index=True)

# Recipient model: relationship('RecipientAlias', back_populates='recipient')
```

4) DataRow serialisation

Vorher: `data` property casts `amount` to `str` and merges `raw_data`.

Nachher: Return a validated Pydantic `DataRowOut` schema that controls formatting and fields, avoids silent overwrites.

**D. Konkrete Refactoring-Vorschläge (konkret + umsetzbar)**
- Einheitliches Timestamp-Pattern: Verwende `server_default=func.now()` und `timezone=True` in allen Modellen; entferne `datetime.utcnow` client-side defaults.
- Replace mutable defaults for JSON columns with `default=lambda: {}` or enforce defaults in the creation logic/service layer.
- Normalize recipient aliases into separate `recipient_aliases` table for faster lookup and cleaner schema.
- Add DB CheckConstraints where applicable: `budget.start_date <= budget.end_date`, `budget.amount > 0`, `transfer.amount > 0` (already present check but ensure positive), `recurring.confidence_score between 0 and 1`.
- Standardize relationships: pick `back_populates` or `backref` and apply consistently. Prefer `back_populates` for explicitness.
- Add unique/index constraints where needed: `import_history.file_hash` unique (if dedup desired), pairing unique constraint for `transfers`.
- Implement Decimal JSON serialization helper (fastapi/pydantic config) to ensure Numeric is converted to string/float consistently and avoid float precision loss.
- Create Pydantic schemas for all models that appear in API responses; remove all `.data` compatibility properties from models and rely on serializers.

**E. Risikobewertung (hoch/mittel/niedrig)**
- Mutable JSON defaults (Category): Medium.
- Inconsistent timezone handling: Medium (can lead to wrong analytics/results across DST/regions).
- Aliases stored as CSV string: Low→Medium (scales badly, query inefficiencies, hard to maintain).
- Missing DB constraints for budgets and some numeric fields: Low→Medium (data corruption risk).
- Duplicate transfer rows allowed (no unique pair constraint): Low→Medium (double counting in stats).

**F. Ungelöste TODOs / Dead Code / Doppelte Logik**
- Keine literal `TODO` Kommentare gefunden in den Modellen; jedoch:
  - Alias handling duplicates logic likely repeated in services (search services likely implement similar normalization) — potential duplicate logic between `Recipient.normalize_name` and service-level normalization.
  - `DataRow.data` legacy property duplicates structured fields and `raw_data` merging (dead/legacy helper) — recommend deprecating and migrating callers to Pydantic serializers.

**G. Beispiele für schnelle, sichere Änderungen (PR-ready)**
1) Add check constraint to `budget`:
```py
from sqlalchemy import CheckConstraint
__table_args__ = (
    CheckConstraint('start_date <= end_date', name='check_budget_date_range'),
)
```

2) Add unique pair constraint to `transfers` (canonicalize ordering or unique together):
```py
from sqlalchemy import UniqueConstraint
__table_args__ = (
    UniqueConstraint('from_transaction_id', 'to_transaction_id', name='uq_transfer_pair'),
)
```

3) Create `recipient_aliases` table and migrate existing CSV aliases into rows (data migration script via Alembic).

---
Ende des `models`-Ordner-Audits. Soll ich nun mit dem nächsten Ordner `routers/` weitermachen? Ich halte hier an (wie gewünscht: Stop nach jedem Folder).

**Integration note**: See `01_backend_overview.md` → "Interplay / System Map" for how models are expected to be used by `services` and `routers`. Key mappings:
- `DataRow` persisted rows are created by `csv_import` (`routers/csv_import.py`) using `CsvProcessor` and `ImportHistoryService`.
- `Recipient` and `RecipientAlias` (recommended) are used by `recipient_matcher` and `category_matcher` in the `services` layer.
- `RecurringTransaction` and its link table are maintained by the `recurring_transaction_detector` service and referenced by API in `routers/recurring.py`.

Please keep this mapping in mind when applying model refactors so service/routers code can be updated in tandem.