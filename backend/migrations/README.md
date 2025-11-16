# Database Migrations

Dieses Verzeichnis enthält alle Datenbank-Migrationen für Money Tracker.

## 📁 Struktur

```
migrations/
├── 001_add_performance_indexes.py    # Performance-Optimierung
├── 002_add_recipients.py             # Recipients-Feature
├── 003_refactor_datarow_structured_fields.py  # DataRow Refactoring
├── run_migrations.py                 # Migration Runner (automatisch)
├── _merged_migration.sql             # Auto-generiert (nicht committen!)
└── README.md                         # Diese Datei
```

## 🔄 Wie Migrations funktionieren

### Automatische Ausführung

Migrations werden **automatisch** beim Backend-Start ausgeführt:

1. Container startet → `entrypoint.sh`
2. Ruft `run_migrations.py` auf
3. Erstellt Tracking-Tabelle `schema_migrations`
4. Findet alle Migration-Files (*.py, *.sql)
5. **Merged SQL-Files** zu einer Datei
6. Führt **Python-Files einzeln** aus
7. Speichert Status in `schema_migrations`

### Tracking-Tabelle

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY,
    version VARCHAR(255) UNIQUE,      -- z.B. "001", "002"
    description TEXT,                 -- z.B. "Add Performance Indexes"
    applied_at TIMESTAMP,             -- Wann ausgeführt
    execution_time_ms INTEGER         -- Wie lange gedauert
);
```

## ✍️ Neue Migration erstellen

### Option 1: SQL Migration

```bash
# 1. Neue Datei erstellen
vim backend/migrations/004_add_user_settings.sql

# 2. SQL schreiben (idempotent!)
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(5) DEFAULT 'de',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user 
ON user_settings(user_id);

# 3. Container neustarten (Migrations laufen automatisch)
docker-compose restart backend
```

### Option 2: Python Migration

```bash
# 1. Neue Datei erstellen
vim backend/migrations/004_complex_migration.py

# 2. Python-Code schreiben
"""
Migration: Complex Data Transformation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def upgrade(conn):
    """
    Main migration function
    Called by run_migrations.py
    """
    print("Running complex migration...")
    
    # Step 1: Add column
    conn.execute(text("""
        ALTER TABLE data_rows 
        ADD COLUMN IF NOT EXISTS normalized_amount NUMERIC(12, 2)
    """))
    
    # Step 2: Populate column
    conn.execute(text("""
        UPDATE data_rows 
        SET normalized_amount = ABS(amount)
        WHERE normalized_amount IS NULL
    """))
    
    conn.commit()
    print("Migration completed!")

if __name__ == "__main__":
    with engine.connect() as conn:
        upgrade(conn)

# 3. Container neustarten
docker-compose restart backend
```

## 📝 Naming Convention

**Format:** `{VERSION}_{DESCRIPTION}.{EXTENSION}`

- **Version:** 3-stellige Zahl (001, 002, 003, ...)
- **Description:** snake_case, kurz und beschreibend
- **Extension:** `.py` oder `.sql`

**Beispiele:**
- ✅ `001_initial_schema.sql`
- ✅ `002_add_recipients.py`
- ✅ `003_refactor_datarow_structured_fields.py`
- ❌ `migration.sql` (keine Version)
- ❌ `01_add_users.sql` (Version zu kurz)
- ❌ `004-add-feature.sql` (Bindestrich statt Underscore)

## ⚠️ Best Practices

### 1. Idempotenz

Migrations sollten **mehrfach ausführbar** sein ohne Fehler:

```sql
-- ✅ Gut
CREATE TABLE IF NOT EXISTS users (...);
ALTER TABLE data_rows ADD COLUMN IF NOT EXISTS status TEXT;
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ❌ Schlecht
CREATE TABLE users (...);  -- Fehler beim 2. Mal!
ALTER TABLE data_rows ADD COLUMN status TEXT;  -- Fehler!
```

### 2. Backwards Compatibility

Vermeide Breaking Changes:

```sql
-- ❌ Schlecht - bricht alte API
ALTER TABLE data_rows DROP COLUMN old_field;

-- ✅ Besser - deprecated aber funktioniert noch
ALTER TABLE data_rows ADD COLUMN new_field TEXT;
-- Alte API nutzt weiter old_field
-- Neue API nutzt new_field
-- Später: remove old_field in separater Migration
```

### 3. Daten-Migration

Immer zuerst Schema, dann Daten:

```python
def upgrade(conn):
    # 1. Schema ändern
    conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"))
    conn.commit()
    
    # 2. Daten migrieren
    conn.execute(text("UPDATE users SET email_verified = TRUE WHERE email IS NOT NULL"))
    conn.commit()
    
    # 3. Constraints hinzufügen
    # (SQLite unterstützt nicht alle ALTER TABLE Befehle)
```

### 4. Performance

Bei großen Tabellen:

```python
# ✅ Batch-Updates
BATCH_SIZE = 1000
offset = 0

while True:
    result = conn.execute(text(f"""
        UPDATE data_rows 
        SET normalized_amount = ABS(amount)
        WHERE id IN (
            SELECT id FROM data_rows 
            WHERE normalized_amount IS NULL 
            LIMIT {BATCH_SIZE}
        )
    """))
    
    if result.rowcount == 0:
        break
    
    conn.commit()
    print(f"Updated {result.rowcount} rows...")
```

### 5. Rollback-Plan

Immer überlegen, wie Rollback funktioniert:

```sql
-- Migration: 004_add_status_column.sql
ALTER TABLE data_rows ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';

-- Rollback (manuell):
-- ALTER TABLE data_rows DROP COLUMN status;
-- Oder mit Python-Migration:
-- def downgrade(conn):
--     conn.execute(text("ALTER TABLE data_rows DROP COLUMN status"))
```

## 🧪 Testing

### Migration lokal testen

```bash
# 1. Backup erstellen
./init_db.sh backup dev "vor_migration"

# 2. Migration testen
docker-compose restart backend
./init_db.sh status

# 3. Bei Fehler: Rollback
./init_db.sh restore backups/moneytracker_dev_TIMESTAMP.db
```

### Migration in Production

```bash
# 1. BACKUP!
./init_db.sh backup prod "vor_migration_$(date +%Y%m%d)"

# 2. Dry-Run im Staging
docker-compose -f docker-compose.staging.yml restart backend

# 3. Wenn OK: Production
docker-compose -f docker-compose.prod.yml restart backend

# 4. Monitoring
./init_db.sh status prod
docker-compose -f docker-compose.prod.yml logs -f backend
```

## 🔍 Status prüfen

### Welche Migrations sind angewandt?

```bash
# CLI-Tool nutzen
./init_db.sh status

# Oder direkt in DB
docker exec moneytracker-backend sqlite3 /app/data/moneytracker.db \
  "SELECT * FROM schema_migrations ORDER BY version"
```

### Migration fehlgeschlagen?

```bash
# 1. Logs prüfen
docker-compose logs backend | grep -i migration

# 2. Status prüfen
./init_db.sh status

# 3. Falls stuck: manuell ausführen
docker exec -it moneytracker-backend python /app/migrations/run_migrations.py
```

## 🐛 Troubleshooting

### Problem: "Table already exists"

**Ursache:** Migration nicht idempotent.

**Lösung:**
```sql
-- Statt:
CREATE TABLE users (...);

-- Nutze:
CREATE TABLE IF NOT EXISTS users (...);
```

### Problem: Migration wird nicht erkannt

**Ursache:** Falsches Naming oder Permissions.

**Prüfen:**
```bash
# 1. Datei vorhanden?
docker exec moneytracker-backend ls -la /app/migrations/

# 2. Naming korrekt?
# Format: 00X_description.{py|sql}

# 3. Executable? (nur relevant für .py)
docker exec moneytracker-backend test -r /app/migrations/004_test.py && echo "readable"
```

### Problem: "No such table: schema_migrations"

**Ursache:** Tracking-Tabelle nicht erstellt.

**Lösung:**
```bash
# Manuell Migration-Runner ausführen
docker exec moneytracker-backend python /app/migrations/run_migrations.py
```

### Problem: Migration hängt

**Symptome:** Backend startet nicht, keine Logs.

**Lösung:**
```bash
# 1. In Container reingehen
docker exec -it moneytracker-backend /bin/bash

# 2. Migration manuell mit Timeout
timeout 60s python /app/migrations/run_migrations.py

# 3. DB-Lock prüfen
sqlite3 /app/data/moneytracker.db "PRAGMA busy_timeout = 5000; SELECT * FROM schema_migrations;"
```

## 📊 Merge-Verhalten

### SQL-Migrations

Werden zu `_merged_migration.sql` zusammengefasst:

```sql
-- Merged Migration File
-- Generated: 2025-11-16T10:30:00

-- ==========================================
-- Migration 001: Add Performance Indexes
-- Source: 001_add_performance_indexes.py
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_account_category ...

-- ==========================================
-- Migration 002: Add Recipients
-- Source: 002_add_recipients.py
-- ==========================================

CREATE TABLE IF NOT EXISTS recipients ...
```

### Python-Migrations

Werden **einzeln** ausgeführt (nicht gemerged).

### Mixed

1. Alle SQL-Migrations → Merge → Einmal ausführen
2. Alle Python-Migrations → Einzeln ausführen

## 📚 Weitere Infos

- **Docker Setup:** Siehe [DOCKER_SETUP.md](../DOCKER_SETUP.md)
- **Improvements:** Siehe [IMPROVEMENTS.md](../IMPROVEMENTS.md)
- **Roadmap:** Siehe [REFACTORING_ROADMAP.md](../REFACTORING_ROADMAP.md)

---

**Zuletzt aktualisiert:** 16. November 2025
