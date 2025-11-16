1) Analyse der Backend‑Struktur
A) API‑Router & Endpunkte

Pattern: Viele Router definieren account‑bezogene Endpunkte mit derselben account‑prüfenden Logik, z.B. account = db.query(Account).filter(Account.id == account_id).first() in fast allen Routern.
Folge: Code‑Duplizierung, inkonsistente Fehlerantworten, hoher Wartungsaufwand.
Inkonsequente Prefix‑Verwendung: main.py bindet manche Router unter /api/v1/accounts (z. B. data, mappings), andere als root unter /api/v1 (z. B. recurring, transfers). Das führt zu unklaren API‑Konventionen und potentiell redundanten Endpfaden.
Response handling: Viele Endpunkte geben ORM‑Objekte zurück (meist Pydantic response_model gesetzt — das ist gut), aber einige Endpunkte bauen freie Dicts zurück; das kann die Konsistenz der API beeinträchtigen.
B) Services / Business‑Logik

Gut: Es gibt zentrale Services (CsvProcessor, DataAggregator, TransferMatcher, MappingSuggester).
Problem: Viele Business‑Regeln sind verteilt und teilweise dupliziert (z. B. Kategorie‑Filter‑Parsing in Routern und im DataAggregator, sowie mehrere Implementierungen für Amount/Date Parsing).
Heavy‑logic in Python loops: TransferMatcher.find_transfer_candidates lädt Transaktionen komplett und führt O(n^2) Python‑Vergleiche aus — funktioniert für kleine Daten, skaliert schlecht.
C) Repository / DB‑Schicht

Es gibt kein dediziertes Repository‑Layer; überall wird mit SQLAlchemy‑Session direkt in Routern und Services gearbeitet.
Vorteile: Einfach zu lesen. Nachteile: Querybau-DSL verstreut, schwer zu testen, Wiederholung von Filter‑Logik.
D) Validierung & DTOs

Pydantic Schemas liegen unter app/schemas/ — viele Endpunkte deklarieren response_model.
Schwächen:
Einige Endpunkte validieren JSON manuell (z. B. mapping_json = Form(...) mit json.loads + Pydantic afterwards) — das ist ok, aber manchmal werden Fehler nicht einheitlich behandelt.
Validierungs‑Logik (z. B. mapping validation, required fields) ist teilweise in Service‑Klassen statt in Pydantic Schemas — besser ist dort, wo möglich, die Validierung dem Schema zu überlassen.
E) Error‑Handling

Viele try/except blocken Exceptions breit ab und wandeln diese in HTTP 400/500 mit generischem Text. Kein zentrales Error‑Logging / Exception‑Handling (z. B. FastAPI exception handlers).
Einige Endpunkte geben aussagekräftige Fehlermeldungen; andere nur generische Serverfehler.
F) Datenbankzugriffe (Queries, Filter, Sortierung)

Queries sind größtenteils SQLAlchemy ORM‑basierend und verwenden Indexes (siehe DataRow.__table_args__).
Wiederholung identischer Filtermuster (Datum, category_id(s), amount range, recipient/purpose ilike, transaction_type).
.count() wird oft auf Query‑Objekten verwendet; für große Tabellen kann count teuer sein.
Einige Abfragen (z. B. TransferMatcher, Ermittlung aller transfer IDs mit .all() gefolgt von Python‑Filter) sind suboptimal.
G) Migrationslogik

Migrations enthalten DB‑features, die nicht auf allen DB‑Backends funktionieren (siehe unten).
Einige SQL in den Migrations ist Postgres‑/advanced‑SQL‑spezifisch (z. B. Partial Index, expression index), kann unter SQLite fehlschlagen.
H) Wiederholte oder doppelte Funktionen (Beispiele)

Account‑Existenzprüfung wiederholt (20+ Vorkommen).
Kategorie‑Filter‑Parsing (single id, CSV string to list with -1 handling) mehrfach implementiert (data.py, data_aggregator.py, dashboard.py ...).
Amount/number parsing: CsvProcessor.normalize_amount vs DataAggregator.parse_amount vs older parse_amount in disabled migration — gleiche Aufgabe mehrfach implementiert.
Recipient search: multiple DataRow.recipient.ilike(...) usage — OK, aber repetitive.
Mapping validation/suggestion vs manual validation — similar code occurs.
I) Inkonsistente Namensgebung

Router prefixes und endpoint url styles nicht 100% konsistent (siehe A).
Einige Model-Attribute vs JSON keys: transaction_date vs legacy date property in DataRow.data (backwards compatibility) — das ist dokumentiert, aber kann zu Verwirrung führen.
J) Bereiche zu stark gekoppelt / unübersichtlich

Routers mischen oft HTTP‑handling + raw DB queries + business logic (z. B. CSV import: Router orchestriert parsing, matching, DB inserts) — das macht einzelne Endpunkte schwer testbar.
Transfer detection logic lebt in service, aber router sometimes also touches transfers; better: single service with clear contract.
K) Unnötige Komplexität

TransferMatcher nested loops → move to SQL approach.
Import: preloading all existing hashes into a Python set — can be memory heavy.
CSV processing uses pandas (appropriate) but lacks file size limits/streaming, so may OOM on large files.
2) Erkennung von Redundanzen — konkrete Fundstellen & Vorschläge zur Zentralisierung
A) Account‑Existenzcheck (highly repetitive)

Fundstellen: ~20 Vorkommen in Routern (data.py, mappings.py, csv_import.py, recurring.py, comparison.py, ...).
Problem: Redundanz + inconsistent error message.
Vorschlag: Erstelle eine FastAPI‑Dependency get_account_or_404(account_id: int, db=Depends(get_db)) -> Account die:
Account lädt oder HTTPException 404 wirft,
Optional prüft Zugriffsrechte,
Rückgabe: Account-Objekt
Vorteil: Entfernt Duplikation, zentralisiert Änderung, verbessert Tests.
B) Kategorie‑Filter‑Parsing (+ handling of -1 uncategorized)

Fundstellen: data.py, data_aggregator.py, dashboard.py, ...
Problem: identische parsing- and filter-building logic duplicated.
Vorschlag: Extra Utility build_category_filter(query, category_id, category_ids) oder ein QueryFilterBuilder-Objekt, das:
Parst category_ids string to list,
Fügt appropriate SQLAlchemy filters to the base query,
Unterstützt uncategorized token (-1) konsistent.
Vorteil: Single source of truth für Kategorie‑Logik; weniger Fehler.
C) Amount / Date parsing & normalization

Fundstellen: CsvProcessor.normalize_amount, DataAggregator.parse_amount, disabled migration helper.
Problem: unterschiedliche Implementationen und leichte Abweichungen → bugs.
Vorschlag: Einzigartige Utility‑Funktionen in app/services/formatters.py:
parse_amount(value) -> Decimal, returns consistent Decimal (do not use float for money).
parse_date(value) -> date (uses same formats).
Vorteil: Einheitliche handler, bessere testbarkeit.
D) Recipient matching / normalization

Normalisierung ist in Recipient.normalize_name aber auch im RecipientMatcher service. Prüfe ob logic doppelt implementiert.
Vorschlag: zentralisiere Normalization in Recipient Model statics; reuse in services.
E) Category mapping / suggestion duplication

MappingSuggester + CategoryMatcher may both have pattern matching logic.
Vorschlag: Extrahiere gemeinsame pattern matching utils (e.g., normalized token match, regex/fuzzy util).
F) Duplicate SQL statements / filters

Viele SQL‑Filter identisch; extrahiere QueryBuilder Funktionen oder Repository‑Methoden wie DataRowRepository.filter_for_account(query, params).
3) Performance‑Analyse — konkrete Probleme & Optimierungen
A) Ineffiziente Abfragen / mögliche Full Table Scans

TransferMatcher: lädt alle Transaktionen (optionally large) and performs nested loops.
Empfehlung: Schreibe SQL‑Query, die für jede negative tx ein join sucht mit positive tx matching abs(amount) and date range and different account; or use windowing / indexed joins.
Getting all transfer_ids via .all() and applying ~DataRow.id.in_(transfer_ids):
If transfer_ids large, IN list performs badly.
Empfehlung: use a subquery / NOT EXISTS: filter(~self.db.query(Transfer).filter(Transfer.from_transaction_id == DataRow.id).exists()) or left outer join and where transfer IS NULL.
B) Missing/ineffective indexes

DataRow indexes are comprehensive (account+date, category+date, recipient, date+amount). Good.
But ilike searches on recipient or purpose may not use index on many DBs (Postgres requires LOWER(...) or trigram/GIN index for fast ilike).
Recommendation:
If Postgres: add GIN trigram index (pg_trgm) on recipient and purpose, or store recipient_normalized lowercased column with btree index and search using equality or prefix.
If SQLite: full-text search (FTS) for text fields.
For row_hash uniqueness check: unique index exists — that's good.
C) Large payloads to frontend

Some endpoints (e.g., CSV preview or data endpoints) may return raw DB models with raw_data JSON field; raw_data may be large — ensure limit or remove raw_data in list endpoints.
Recommendation: For list endpoints, exclude heavy fields by constructing projection queries or Pydantic schemas that hide raw_data.
D) Unnecessary JSON transformations

DataRow.data property merges structured fields and raw_data — can create large nested objects. Prefer explicit shape per endpoint.
E) Counting & pagination

.count() + .limit().all() pattern: two queries — expensive but standard. For very large datasets, consider:
Using estimated counts (Postgres ANALYZE) or approximate counts for UX,
Or cursor-based pagination to avoid count queries.
F) CSV import memory use

Current import loads full CSV into pandas DataFrame. For large files, memory pressure.
Recommendation: enforce server-side size limit; consider chunked processing or streaming (e.g., read_csv with chunksize).
4) Architektur‑Verbesserungen (konkrete Vorschläge)
A) Schichten / Modularisierung

Introduce light Repository layer for DataRow/Transfer/ImportHistory etc. (e.g., data_row.py) that exposes expressive methods:
filter_data_rows(session, filters), get_total_count_for_filters(session, filters), bulk_insert_rows(session, rows).
Benefits: centralize queries, easier caching and testing.
B) Einheitlicher Filter‑/Query‑Builder

Implement QueryFilters helper that translates request params into SQLAlchemy filters once, reused across routers and aggregator.
Accept input DTO (Pydantic) for filter params.
C) Account dependency

As above, get_account_or_404 and optionally get_account_or_403 for auth later.
D) Error handling

Add global FastAPI exception handlers for:
ValidationError → 422
DomainError (custom exceptions) → mapped status codes
Unexpected Exception → 500 with logging
Centralize error logging (Sentry or structured logs).
E) DTOs / Response shaping

Use Pydantic models for all responses; avoid returning raw DB objects in list endpoints. Create "light" list DTOs that omit raw_data and heavy fields.
F) Query‑builder or ORM helpers for aggregations

For heavy aggregations (category aggregation, recipient aggregation), prefer doing as much as possible in SQL and use repository functions.
G) Concurrency / Transactions

For multi-step operations (CSV import): wrap DB changes in transaction (commit at the end), handle integrity errors (unique row_hash) instead of loading full hash set.
5) Robustheit & Wartbarkeit — konkrete Risiken & Fixes
A) Missing validations

Some parsers raise generic exceptions; prefer pydantic validation earlier.
Mapping JSON parsing in router uses json.loads + Pydantic — fine, but ensure robust error messages.
B) Error handling & logging

Add central logging and structured error messages, reduce broad excepts.
C) Race conditions

CSV import uses:
prefetch existing_hashes set (race with concurrent imports), then inserts relying on in-memory duplicate check. If two imports happen concurrently, duplicates can be inserted unless DB constraint stops it — DB will raise integrity error. Need to handle constraint exceptions gracefully (rollback single row or batch).
Mappings save: delete then insert — no transaction or race safety. Wrap in transaction.
D) Fragile code paths

Transfer detection nested loops are fragile and expensive.
DataRow.data property merging raw JSON may mask field name collisions.
E) Type mismatches

Monetary fields use Numeric but code converts to Python float in places (e.g., _serialize_transaction returns float(tx.amount)) — recommend using Decimal consistently.
6) Datenbank & Migrationslogik — konkrete Probleme & Vorschläge
A) Migrations incompatibilitäten (kritisch)

007_add_transfers.sql enthält:
CREATE UNIQUE INDEX with expression MIN(from_transaction_id, to_transaction_id) / MAX(...) — this is not standard SQL and will fail on SQLite and many DBs. Creating a unique constraint that enforces pairing in both orders is tricky in SQL; the current syntax is invalid.
Fix: store normalized pair ordering in table (e.g., columns pair_min_id and pair_max_id computed on insert) or create a check + unique constraint approach in DB that both DB engines support; or use application-level guard with DB unique index on ordered tuple by normalizing order before insert.
008_add_insights.sql uses partial indexes (WHERE is_dismissed = 0) — partial indexes exist in Postgres but not in SQLite. If project runs SQLite in dev and Postgres in prod, migrations must be conditional.
Triggers / CHECK constraints syntax differ slightly across DBs. Tests needed for target DB.
B) Foreign keys & ON DELETE semantics

Most FKs include ON DELETE behavior — good.
Ensure DB supports it (SQLite requires PRAGMA foreign_keys=ON, but SQLAlchemy engine for SQLite should set it).
C) Indexes

DataRow model defines many indexes — good.
Missing: if heavy ilike usage, need trigram/GIN index on Postgres or FTS on SQLite as mentioned.
D) Normalization & table design

raw_data JSON retained — good for audit, but consider storing only trimmed raw data if size is a concern.
Recipient model stores aliases as comma-separated string — reduce normalization issues by using a child recipient_aliases table for efficient lookups and indexing for many aliases.
E) Migration idempotency / ordering

Migrations use CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS — that's fine.
But reliance on DB‑specific features requires migration engine awareness. Suggest moving to a migration tool (Alembic) if not used, or create separate SQL for SQLite vs Postgres.
Auffällige, konkrete Code‑Bugs / Blocker
Migration 007's unique index on MIN/MAX is invalid SQL and will break migrations. Das ist ein kritischer Blocker für reproduzierbare DB‑Setup.
Migration 008 uses partial indexes unsupported by SQLite. If your default dev DB is SQLite, this will either error or be ignored—needs conditional migrations.
TransferMatcher and other services performing O(n^2) python loops will not scale.