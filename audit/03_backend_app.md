**TL;DR:**
- `backend/app` enthält die Hauptanwendung: Konfiguration, DB-Setup, FastAPI-App, Datenmodelle, Router und Utility-Funktionen. Gute Basis; Verbesserungspotenzial bei Validierung, Migrations-Workflow, Security-Hardening und Typisierung.
**A. Zusammenfassung**
**Integration note**: See `01_backend_overview.md` → "Interplay / System Map" for the canonical integration mapping between `main.py`, `routers`, `services`, `models`, `schemas`, `utils`, and `migrations`. Use that file as the source of truth when reconciling cross-file recommendations.
**B. Tiefgehende Datei-für-Datei Analyse (Wichtigste Dateien)**

- `config.py`
  - Zweck: zentrales Settings-Objekt (`settings`) basierend auf Pydantic `BaseSettings`.
  - Wichtige Felder: `DATABASE_URL`, `BACKEND_CORS_ORIGINS`, `HOST`, `PORT`, `SENTRY_DSN`, Pagination-Limits.
  - Auffälligkeiten:
    - `DATABASE_URL` Default `sqlite:///./moneytracker.db` im Code — sinnvoll lokal, sollte aber in Prod nicht verwendet werden.
    - `parse_cors_origins` implementiert flexible Parsing (JSON array oder CSV string) — gut.
    - Logging maskiert DB-URL vor Ausgabe (`_mask_db_url`) — gut.

- `database.py`
  - Zweck: Engine, `SessionLocal`, Base.
  - Auffälligkeiten:
    - `is_sqlite` detection ist heuristisch, funktioniert in den meisten Fällen.
    - `connect_args = {"check_same_thread": False}` bei SQLite — korrekt.
    - `SessionLocal = sessionmaker(...)` Standardkonfiguration; `future=True` im engine, aber sessionmaker nicht mit `future=True` explizit (Session behavior is classic vs 2.0 style) — Empfehlung: `sessionmaker(class_=AsyncSession, future=True)` wenn AsyncSession gewollt.
  - Verbesserungsvorschläge:
    - Explizite DB-Engine-Konfigurationsmatrix (Postgres/MySQL) in `config`.
    - Add health-check / retry logic for engine creation in containerized env.

- `main.py`
  - Zweck: App-Initialisierung, Lifespan, Router-Registrierung, Error-Handling.
  - Positive Aspekte:
    - Sauberer Error-Wrapping in `_format_error_response` und drei exception handlers.
    - Health endpoints with both liveness and readiness (DB check).
    - Optional Sentry integration guarded by `settings.SENTRY_DSN`.
  - Probleme / Risiken:
    - `Base.metadata.create_all` wird im lifespan verwendet — migrations/ale mbic vorhanden → workflow-inkonsistenz.
    - Direkte Imports vieler Router-Module zusammen in `main.py` erhöhen Kopplung. Besser: discover/register pattern oder zentraler `routers.__init__`.
    - `metrics()` endpoint returns 501 if `prometheus_client` missing — OK for optional dependency, but should be consistent in docs.

- `models/` (Kurzbewertung):
  - Allgemein: gut modelliert mit timestamps und Kommentaren.
  - Spezifische Hinweise:
    - `Category.mappings` JSON default uses Python dict as default — server default vs client default caveat. For mutable default use `default_factory` or handle in application layer.
    - Use of `Numeric` in SQLAlchemy: ensure consistent serialization/deserialization (Decimal vs float) in pydantic/JSON responses.

**C. Codebeispiele (Problems & Fixes)**
- JSON default mutability and DB default inconsistency

Vorher (in `models/category.py`):
```py
mappings = Column(
    JSON,
    nullable=False,
    default={"patterns": []},
    comment="Pattern list for automatic categorization"
)
```

Problem: `default` uses a mutable dict and is applied client-side; for some dialects this won't set DB-side default and can cause identical object reuse.

Nachher (Empfehlung):
```py
from sqlalchemy import column
from sqlalchemy.sql import expression

# Option A: application-level default
mappings = Column(JSON, nullable=False, server_default=expression.text('json("[]")'), default=lambda: {"patterns": []})

# Option B: enforce in __init__ or via pydantic layer
```

- Guard `create_all` behind ENV

Vorher (in `main.py`):
```py
await asyncio.to_thread(Base.metadata.create_all, bind=engine)
```

Nachher:
```py
if settings.ENV == 'development' and settings.AUTO_CREATE_TABLES:
    await asyncio.to_thread(Base.metadata.create_all, bind=engine)
else:
    get_logger('app.main').info('Skipping create_all; migrations expected')
```

**D. Refactoring-Vorschläge (konkret + umsetzbar)**
- Introduce `app/factory.py` or `app/__init__.py`-funktion `create_app(settings)` returning FastAPI instance — erleichtert tests und reuse.
- Move router registration into `app/routers/__init__.py` with `register_routers(app)`.
- Add typed service layer interfaces (z. B. `Services` folder) that accept `Session` and return Pydantic models.
- Replace `Base.metadata.create_all` with explicit migration-run step or guard via ENV var.
- Add util to convert SQLAlchemy `Decimal` values to floats/strings consistently when returning JSON (or use Pydantic model with Decimal handling).

**E. Risikobewertung (per file)**
- `config.py` — Default secrets in code: Medium
- `database.py` — Missing DB retry/health tuning: Low→Medium
- `main.py` — `create_all` in production: Medium→High
- `models/` — Incorrect JSON defaults or Numeric handling: Low→Medium

**F. Ungelöste TODOs / FIXME / Dead Code**
- Keine expliziten `TODO`/`FIXME` Kommentare in den gelesenen Dateien, aber Hinweise auf:
  - Migrations vs `create_all` Inkonsistenz (migrations/ existiert)
  - Optional libs (`prometheus_client`, `sentry_sdk`) die evtl. fehlen, sollten optional im requirements dokumentiert werden.

**G. Nächste Schritte / Empfehlungen**
- Ich empfehle: (1) Migrations-Workflow klar dokumentieren (README/CI); (2) ENV-Guard für `create_all`; (3) Add pydantic models for all responses; (4) Add security audit (CORS, secrets handling); (5) Add type hints/typing in service layer.

---
Ich habe die wichtigsten Dateien des `backend/app`-Ordners analysiert und ein initiales Audit erzeugt. Soll ich nun weiter in `backend/app/routers` und `services` jede Datei einzeln lesen und für jeden Unterordner eine eigene Markdown-Datei erzeugen (wie gewünscht)?