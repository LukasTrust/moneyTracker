**TL;DR:**
- `backend/app/services` implementiert die Business-Logic: CSV-Parsing, Hashing, Mappings, Matching (Category/Recipient/Transfer), Aggregation, Recurring-Detection, Insights-Generierung und Job-Tracking.
- Der Code ist funktional und domänenspezifisch gut aufgebaut, aber es gibt mehrere Wartbarkeits-, Performance- und Portabilitäts-Probleme: Verwendung von `float` statt `Decimal` für Geld, speicherintensive Pandas-Operationen für große CSVs, DB-dialekt-spezifische SQL (e.g. `strftime`), vollständiges Laden großer Tabellen in Python (Recipient matching), sowie inkonsistente Zeitstempel/Timezone-Handling.

**A. Zusammenfassung (Manager TL;DR)**
- Services decken alle Kernfunktionen ab (Import, Kategorisierung, Matching, Aggregation, Insights, Recurring Detection).
- Kurzfristige Maßnahmen: Zentralisieren von Money-Types auf `Decimal`, begrenzen von CSV-Upload-Größen / Stream-Verarbeitung, Migration von alle-für-alles queries zu DB-gestützten Aggregaten oder paginierten/limit-Queries, und Einführung von Tests für Grenzfälle.

**B. Datei-für-Datei Analyse**

1) `hash_service.py` — Zweck
- SHA256-Hash für Duplikaterkennung, basiert auf `json.dumps(data, sort_keys=True, ensure_ascii=False)`.

Probleme / Verbesserungen:
- Hash-Stabilität: Wenn `data` enthält: float vs Decimal vs unterschiedliche String-Repräsentationen, dieselben semantischen Werte können unterschiedliche Hashes erzeugen. Empfehlung: Normalisiere Werte (z. B. `Decimal` quantize oder formatierte Strings) bevor gehasht wird.

Beispiel (Verbesserung):
Vorher:
```py
sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
```
Nachher (empfohlen):
```py
from decimal import Decimal
# normalize amounts explicitly
norm = {k: (str(v) if not isinstance(v, Decimal) else format(v, 'f')) for k, v in data.items()}
sorted_data = json.dumps(norm, sort_keys=True, ensure_ascii=False)
```

Risikobewertung: Niedrig → Medium (duplikaterkennung kann fehlschlagen, wenn nicht normalisiert).


2) `csv_processor.py` — Zweck
- CSV-Parsing, Encoding/Delimiter-Detection, Mapping-Anwendung, Daten-Normalisierung (Datum, Betrag), Preview-Funktionen.

Wichtige Beobachtungen:
- Abhängigkeiten: `pandas`, `chardet` —— überprüfen, ob in `requirements.txt` gelistet.
- `pd.read_csv(..., dtype=str)` liest alles als Strings — bewusst, aber: `normalize_amount` wandelt Strings mit `float` zurück, das kann zu Rundungsfehlern führen. Empfehlung: Verwende `Decimal` für monetäre Werte durchgängig.
- `normalize_amount` behandelt deutsch/englische Formate gut, aber verwendet `float` und fängt Fehler still mit `return 0.0` ab — das verschleiert fehlerhafte Eingaben.
- `parse_csv_advanced` versucht mehrere Encodings/Delimiters — gut, aber lädt das komplette File in `pandas.DataFrame` und kann bei großen Dateien viel RAM verbrauchen. Für große CSVs sollte ein Streaming-Parser (e.g. Python csv module + chunking) eingesetzt werden.
- Sicherheits-/Stabilitätsrisiken: Keine Dateigrößen-Limits oder timeouts → DoS-Vektor; `on_bad_lines='warn'` kann fehlerhafte Zeilen verdecken.
- `parse_date` ist robust, gibt aber `None` bei unbekannten Formaten — `normalize_transaction_data` wirft dann `ValueError` (gute behavior), aber auf API-Ebene sollten die Fehler klar zurückgegeben werden.

Konkrete Verbesserungen:
- Verwende `Decimal` anstelle von `float` für `amount` und bewahre präzise Strings in DB (oder konvertiere in Decimal mit quantize).
- Implementiere chunked parsing: `pd.read_csv(..., chunksize=...)` oder nutze `csv`/`DictReader` für streaming.
- Setze ein Maximum-File-Size-Limit und explizite Fehlerausgaben bei fehlerhaften Zeilen.
- Explizite Fehlerliste zurückgeben statt `return 0.0` bei InvalidAmount.

Codebeispiel (Streaming-Parser):
```py
import csv
from decimal import Decimal

def stream_parse(file_stream):
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))
    for row in reader:
        # minimal validation and yield normalized rows
        yield CsvProcessor.normalize_transaction_data(row)
```

Risikobewertung: Hoch (Speicher- und Performance-Risiko bei großen Uploads; precision-errors bei Finanzen).


3) `category_matcher.py` — Zweck
- Matching von Transaktionen zu Kategorien mittels Regex-Patterns (aus `Category.mappings.patterns`).

Beobachtungen:
- Precompiling und Caching ist korrekt implementiert; `clear_cache()` existiert.
- Patterns werden lowercased and escaped — gut für literal matches, jedoch limitiert wenn Patterns regex-intentiert sind.
- Fehlerhafte Regex werden still übersprungen (good resilience).

Verbesserungen:
- Normalize patterns (strip, NFC unicode normalization) beim Speichern/Seeding.
- Allow configurable matching modes (exact, contains, fuzzy) — currently only word-boundary literal matching.

Risikobewertung: Niedrig → Medium (matching accuracy kann je nach pattern quality variieren).


4) `data_aggregator.py` — Zweck
- Aggregationen für Dashboard / Statistik: summary, category aggregation, recipient aggregation, balance history, period comparisons.

Wichtige Probleme:
- Dialektabhängigkeit: Nutzung von `func.strftime(date_format, DataRow.transaction_date)` — funktioniert in SQLite, aber nicht in Postgres (Postgres nutzt `to_char` oder `date_trunc`). Portabilitätsrisiko.
- Extensive use of Python iteration on ORM resultsets (e.g., get_recipient_aggregation loads all matched DataRow rows) — memory/latency issues for large datasets. Many aggregation steps could be expressed purely with SQL and retrieved already aggregated.
- Floats: Konvertiert DB-Numeric zu float oft; recommend Decimal.
- Repeating filter-building logic across multiple methods — duplicate code; should extract filter builder helper to reduce bugs.

Refactoring-Vorschläge:
- Implement DB-agnostic grouping via SQLAlchemy functions mapping per-dialect, or provide two implementations depending on `engine.dialect.name`.
- Move complex per-row calculations into SQL using `GROUP BY` and DB functions; reduce data movement.
- Extract common filter-building into helper method to avoid copy-paste.

Codebeispiel (reduce duplication):
```py
def _apply_common_filters(query, filters):
    if filters.account_id:
        query = query.filter(DataRow.account_id == filters.account_id)
    # ... other filters
    return query
```

Risikobewertung: Medium → High (scales poorly on large datasets; portability issues).


5) `hash_service.py` already covered above.


6) `import_history_service.py` — Zweck
- Erzeugung/Update von Import-History-Einträgen und Rollback-Operationen.

Beobachtungen:
- `create_import_record` generiert `file_hash` korrekt, commitet direkt und returned das Objekt.
- `rollback_import` verwendet `db.query(DataRow).filter(DataRow.import_id == import_id).delete()` — möglicherweise problematisch, weil `query.delete()` bypasses ORM cascade semantics in some configs; prefer `session.query(...).delete(synchronize_session=False)` and ensure related rows are handled or use `session.execute` with caution.
- `check_duplicate_file` uses `file_hash` equality — if `file_hash` not enforced unique at DB-level, race conditions may allow duplicates. Consider unique index on `(account_id, file_hash)` and handle IntegrityError on insert.

Verbesserungen:
- Add unique index on `ImportHistory(file_hash, account_id)` if dedup is desired.
- Use transactional boundaries and explicit error handling for `rollback_import`.
- Return structured errors instead of ValueError to map to HTTP statuses.

Risikobewertung: Medium (data integrity during concurrent imports).


7) `insights_generator.py` — Zweck
- Algorithmen zur Generierung von Insights (MoM, YoY, Kategorie-Wachstum, Sparpotential).

Beobachtungen:
- Umfangreiche und gut konzipierte Heuristiken; Cooldown-Mechanismus und caching vorhanden.
- Viele ORM-Queries, some loops -> potential performance concerns. For example `_get_category_expenses` queries and returns a dict then `generate_category_growth_insights` compares with previous period — okay but expensive for many categories/accounts.
- Uses `Insight` ORM object instances created in-memory and later converted — consider building `Insight` instances with proper session handling or returning DTOs directly.
- Deletion and cleanup use `query.delete` (synchronize_session=False in some places) — consistent behavior should be verified.

Verbesserungen:
- Move heavy batch calculations to background workers (Celery/RQ) if generation is expensive.
- Ensure index coverage on `DataRow.transaction_date`, `category_id`, `account_id` (exists) for queries used.
- Add tests for thresholds and edge-cases (e.g., small sample sizes, zero prev month expense).

Risikobewertung: Medium (performance + correctness under edge cases).


8) `job_service.py` — Zweck
- Simple job table operations for background tasks.

Probleme:
- Uses `db.query(BackgroundJob).get(job_id)` — `.get()` is deprecated in SQLAlchemy 2.x style, prefer `db.get(BackgroundJob, job_id)`.
- Timestamps use `datetime.utcnow()` (naive) while other parts use timezone-aware `func.now()`.

Verbesserungen:
- Use consistent timezone-aware timestamps.
- Consider linking to an external job queue (RQ/Celery) for robust background processing.

Risikobewertung: Low → Medium (technical debt + minor bugs in future SQLAlchemy versions).


9) `mapping_suggester.py` — Zweck
- Suggest CSV header mapping using heuristics and fuzzy matching.

Beobachtungen:
- Good coverage of keywords and fuzzy logic. SequenceMatcher is OK for small header lists.
- Could be improved by using tokenization and trigram matching for robustness.

Risikobewertung: Low.


10) `recipient_matcher.py` — Zweck
- Normalize/find/create recipients, fuzzy matching, alias handling, merging.

Probleme:
- Full-table `self.db.query(Recipient).all()` for fuzzy matching — does not scale.
- `aliases` stored as CSV string — poor for indexing and searching (recommend separate `recipient_aliases` table or JSON array column with index support).
- After finding similar recipient, `add_alias` updates CSV-string and commits; this may produce duplicated aliases or inconsistent normalization across entries.

Verbesserungen:
- Use DB-level fuzzy search (trigram, pg_trgm) or full-text index, or at least restrict candidate set with `normalized_name LIKE 'prefix%'` before fuzzy compare.
- Store aliases in their own table and index alias column.

Risikobewertung: Medium (scaling + maintenance costs).


11) `recurring_transaction_detector.py` — Zweck
- Identify recurring transactions (monthly subscriptions, rent, etc.) and create/update `RecurringTransaction` entries.

Beobachtungen:
- Algorithm is pragmatic and uses amount similarity, interval detection and thresholds. Good design with `MIN_OCCURRENCES` etc.
- Potential performance cost for accounts with many transactions; algorithm uses in-Python loops (but only per-account and grouping by recipient) which is acceptable if run as background job.
- Use of `SessionLocal()` in background runner is acceptable; ensure background tasks are rate-limited and have error handling (there is try/except logging which is good).

Edge cases / improvements:
- Replace naive amount grouping with clustering (e.g., bucketing by rounded amount) to avoid collisions.
- Use DB-side queries to limit candidate transactions (e.g., last N months) before loading into Python.
- Avoid rounding to integer for map keys as it can merge distinct amounts.

Risikobewertung: Medium.


12) `transfer_matcher.py` — Zweck
- Detect and create transfers between accounts.

Probleme / Verbesserungspunkte:
- Uses exact equality `DataRow.amount == abs(tx1.amount)` for matching amounts. With `Numeric`/`Decimal` columns, comparing to floats may produce mismatch; use Decimal and/or tolerance (e.g., between `abs(tx1.amount) - 0.01` and `+0.01`).
- `existing_transfer_ids` retrieval via union and `.all()` may produce large lists — prefer DB-side anti-join to filter out already linked transactions.
- `_serialize_transaction` converts to `float(tx.amount)` — rounding/precision risk.
- `_calculate_text_similarity` is simple word-overlap; could be improved with tokenization and normalization.

Security/Correctness:
- `create_transfer` enforces same-amount equality strictly; consider small rounding tolerances or normalizing amounts before comparison.

Risikobewertung: Medium → High (incorrect matches or failures to match due to numeric mismatches).


**C. Konkrete Codebeispiele (Vorher / Nachher)**

1) Use Decimal for amounts (everywhere)
Vorher (CsvProcessor.normalize_amount):
```py
return float(amount_str)
```
Nachher (empfohlen):
```py
from decimal import Decimal, InvalidOperation

try:
    # normalize dot/commas first as existing logic, then convert to Decimal
    return Decimal(amount_str)
except InvalidOperation:
    raise ValueError("Invalid amount format")
```

2) Stable hash generation (HashService)
Vorher:
```py
sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
```
Nachher:
```py
from decimal import Decimal

def _normalize_for_hash(data):
    out = {}
    for k, v in sorted(data.items()):
        if isinstance(v, Decimal):
            out[k] = str(v.normalize())
        elif isinstance(v, float):
            out[k] = format(v, '.2f')
        else:
            out[k] = v
    return json.dumps(out, sort_keys=True, ensure_ascii=False)

sorted_data = _normalize_for_hash(data)
```

3) Transfer matching tolerant comparison
Vorher:
```py
if abs(from_tx.amount) != to_tx.amount:
    raise ValueError("Transaction amounts must match (inverted)")
```
Nachher:
```py
from decimal import Decimal

if not (Decimal(abs(from_tx.amount)).quantize(Decimal('0.01')) == Decimal(to_tx.amount).quantize(Decimal('0.01'))):
    raise ValueError("Transaction amounts do not match within tolerance")
```


**D. Refactoring-Vorschläge (konkret & umsetzbar)**
- Migrate all money fields/processing to `Decimal` and centralize decimal config (context & quantize rules). Update schemas to `Decimal` and configure Pydantic JSON encoders.
- CSV parsing: implement stream-based parsing for large files; optionally add a max-file-size config in `settings` and return 413 for too-large files.
- Move heavy computations to background tasks (use `job_service` plus a worker queue) and mark endpoints to return job id for progressive results.
- Add DB indexes and unique constraints where necessary (e.g., `ImportHistory(file_hash, account_id)` unique; `Transfer` unique pair constraint)
- Replace `.all()` loads for fuzzy searches with restricted candidate queries or use DB-side fuzzy search (Postgres pg_trgm) and pagination.
- Abstract dialect-specific SQL (strftime vs date_trunc) behind a small helper util to keep `DataAggregator` DB-agnostic.
- Add explicit error classes (e.g., `ServiceError`) and map them to HTTP responses centrally instead of raising `ValueError`.
- Replace deprecated SQLAlchemy `.get()` calls with `session.get(Cls, pk)`.


**E. Risikobewertung (Gesamt)**
- Performance (large CSVs, full-table scans): Hoch
- Numeric precision issues (floats vs Decimal): Hoch
- Portability (SQLite-specific SQL): Medium
- Data integrity (concurrent imports, lack of unique file_hash constraint): Medium
- Security (unbounded uploads, potential CSV-injection on exports): Medium


**F. TODOs / Quick Wins (PR-Vorschläge)**
- [ ] Replace `float` with `Decimal` in `csv_processor`, `data_aggregator`, `transfer_matcher`, `insights_generator`, and schemas.
- [ ] Add `requirements.txt` check to ensure `pandas`, `chardet`, `python-dateutil` are present and pinned.
- [ ] Implement file-size limit and streaming CSV parsing (use `chunksize` or `csv.DictReader`) to avoid OOM.
- [ ] Add unique index `(account_id, file_hash)` on `import_history` and handle IntegrityError on insert.
- [ ] Replace `strftime` usage with a dialect-agnostic helper in `data_aggregator`.
- [ ] Migrate recipient aliases to normalized alias table and add trigram/full-text search for fuzzy matching.
- [ ] Add integration tests for CSV parsing edge cases and transfer matching with Decimal tolerance.


**G. Schlussbemerkungen & Nächste Schritte**
- Ich habe das `services`-Verzeichnis komplett analysiert und die Datei `/audit/05_backend_services.md` erstellt.
- Vorschlag: Als nächstes Ordner `routers/` analysieren (dort sind API-Endpunkte, Request-Handling, Fehler-Mapping und direkte Service-Aufrufe sichtbar). Soll ich damit weitermachen? Wenn ja, beginne ich Datei-für-Datei und erstelle einzelne Audit-MDs pro Router-Ordner (wie gewünscht).

**Integration note**: See `01_backend_overview.md` → "Interplay / System Map" for canonical component interactions. Practical crosschecks for services:
- Ensure services accept and return Pydantic models or primitive DTOs that match `schemas/*` to keep routers thin and API contracts stable.
- When changing storage models (e.g., migrating `Recipient.aliases` to a normalized `recipient_aliases` table), update the related services (`recipient_matcher`, `mapping_suggester`, `csv_import`), routers, and migration steps together.
- After migrating to `Decimal`, update `HashService`, `TransferMatcher`, and all aggregators to normalize values before hashing/comparing.
