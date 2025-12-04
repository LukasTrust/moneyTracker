# Erweiterte Vergleichsanalysen

Diese Erweiterung fügt drei neue Vergleichstypen zur bestehenden Comparison-Seite hinzu:

## 🎯 Neue Features

### 1. **Benchmark-Analyse**
Vergleicht die aktuellen Ausgaben mit historischen Durchschnittswerten.

**Features:**
- Vergleich der Gesamtausgaben mit dem historischen Durchschnitt
- Kategorienweise Benchmark-Analyse
- Visuelle Indikatoren (über/unter Durchschnitt)
- Prozentuale Abweichungen
- Insights und Empfehlungen

**API-Endpunkt:**
```
GET /api/comparison/{account_id}/benchmark?year=2024&month=12
```

**Parameter:**
- `year` (optional): Jahr für Benchmark (Standard: aktuelles Jahr)
- `month` (optional): Monat für spezifischeren Benchmark (1-12)

### 2. **Mehrjahres-Vergleich**
Vergleicht mehrere Jahre gleichzeitig mit Trendanalyse.

**Features:**
- Vergleich von 2-5 Jahren
- Jahr-zu-Jahr Veränderungen
- Durchschnittswerte über alle Jahre
- Balkendiagramme (Einnahmen vs. Ausgaben)
- Liniendiagramm für Nettosaldo-Trend
- Detaillierte Jahresübersicht

**API-Endpunkt:**
```
GET /api/comparison/{account_id}/multi-year?years=2023,2024,2025
```

**Parameter:**
- `years` (erforderlich): Komma-separierte Liste von Jahren
- `top_limit` (optional): Anzahl der Top-Empfänger (Standard: 5)

### 3. **Quartalsvergleich**
Vergleicht Quartale innerhalb eines Jahres, optional mit dem Vorjahr.

**Features:**
- Vergleich aller 4 Quartale eines Jahres
- Quartals-zu-Quartal Veränderungen
- Optionaler Vergleich mit Vorjahresquartalen
- Durchschnittliche Quartalseinnahmen/-ausgaben
- Detaillierte Quartalsübersicht mit Kategorien
- Visuelle Balkendiagramme

**API-Endpunkt:**
```
GET /api/comparison/{account_id}/quarterly?year=2024&compare_to_previous_year=true
```

**Parameter:**
- `year` (erforderlich): Jahr für Quartalsvergleich
- `compare_to_previous_year` (optional): Vergleich mit Vorjahr (Standard: false)

## 🏗️ Architektur

### Backend-Komponenten

#### Router (`backend/app/routers/comparison.py`)
Neue Endpunkte:
- `GET /{account_id}/benchmark` - Benchmark-Analyse
- `GET /{account_id}/multi-year` - Mehrjahres-Vergleich
- `GET /{account_id}/quarterly` - Quartalsvergleich

#### Service (`backend/app/services/data_aggregator.py`)
Neue Methoden:
- `get_benchmark_analysis()` - Berechnet Benchmark-Daten
- `get_multi_year_comparison()` - Berechnet Mehrjahres-Vergleich
- `get_quarterly_comparison()` - Berechnet Quartalsvergleich

### Frontend-Komponenten

#### Services (`frontend/src/services/comparisonService.js`)
Neue API-Funktionen:
- `getBenchmarkAnalysis()`
- `getMultiYearComparison()`
- `getQuarterlyComparison()`

#### Komponenten
1. **`BenchmarkAnalysis.jsx`**
   - Zeigt Benchmark-Vergleich an
   - Kategorienweise Abweichungen
   - Visuelle Indikatoren und Insights

2. **`MultiYearComparison.jsx`**
   - Mehrjahres-Übersicht
   - Trend-Charts (Bar und Line Charts)
   - Jahr-zu-Jahr Änderungen
   - Detaillierte Jahrestabelle

3. **`QuarterlyComparison.jsx`**
   - Quartalsübersicht mit Charts
   - Quarter-to-Quarter Änderungen
   - Vorjahresvergleich (optional)
   - Detaillierte Quartalskarten

4. **`ComparisonView.jsx` (erweitert)**
   - Moduswahl: Standard / Mehrjahres / Quartals / Benchmark
   - Dynamische Controls basierend auf Modus
   - Automatisches Laden bei Änderungen

## 📊 Verwendungsbeispiele

### Benchmark-Analyse
```javascript
// Frontend
const data = await getBenchmarkAnalysis(accountId, 2024, 12);

// Zeigt:
// - Aktuelle Ausgaben: 2.500€
// - Durchschnitt: 2.100€
// - Differenz: +400€ (+19%)
// - Kategorie "Lebensmittel": +15% über Durchschnitt
```

### Mehrjahres-Vergleich
```javascript
// Frontend
const data = await getMultiYearComparison(accountId, [2023, 2024, 2025]);

// Zeigt:
// - Trend über 3 Jahre
// - 2023 → 2024: Einnahmen +5%
// - 2024 → 2025: Ausgaben -3%
// - Durchschnittliche Einnahmen: 45.000€/Jahr
```

### Quartalsvergleich
```javascript
// Frontend
const data = await getQuarterlyComparison(accountId, 2024, true);

// Zeigt:
// - Q1-Q4 im Jahr 2024
// - Vergleich mit Q1-Q4 2023
// - Q1 2024 vs Q1 2023: Ausgaben +8%
// - Durchschnittliche Quartalsausgaben: 12.500€
```

## 🎨 UI/UX Features

### Moduswahl
Vier Buttons am Anfang der Seite:
- **Standard-Vergleich**: Bestehende 2-Perioden-Vergleichsfunktion
- **Mehrjahres-Vergleich**: Neue Mehrjahres-Funktion
- **Quartalsvergleich**: Neue Quartalsfunktion
- **Benchmark**: Neue Benchmark-Funktion

### Dynamische Bedienelemente
- **Standard**: Dropdown für Monat/Jahr-Wahl
- **Mehrjahres**: Jahr-Auswahl (Buttons)
- **Quartals**: Jahr-Dropdown + Checkbox für Vorjahresvergleich
- **Benchmark**: Jahr + Monat Dropdown

### Visualisierungen
- Recharts für interaktive Diagramme
- Farbcodierte Karten (grün/rot für positive/negative Änderungen)
- TrendingUp/TrendingDown Icons für visuelle Hinweise
- Prozentbalken für Benchmark-Abweichungen

## 🚀 Nutzung

1. **Navigation**: Gehe zu einem Account und öffne den "Vergleichen"-Tab
2. **Modus wählen**: Wähle einen der vier Vergleichsmodi
3. **Parameter einstellen**: Konfiguriere die gewünschten Parameter (Jahre, Quartale, etc.)
4. **Analyse**: Die Daten werden automatisch geladen und visualisiert

## 💡 Insights & Empfehlungen

Alle drei neuen Modi bieten:
- **Automatische Insights**: Wichtige Erkenntnisse werden hervorgehoben
- **Vergleichsmetriken**: Prozentuale Änderungen und absolute Werte
- **Trend-Analyse**: Entwicklungen über Zeit erkennen
- **Kategorien-Breakdown**: Detaillierte Aufschlüsselung nach Kategorien

## 🔧 Technische Details

### Berechnungslogik

**Benchmark:**
- Berechnet historische Durchschnitte (alle Daten außer aktueller Periode)
- Vergleicht aktuelle Periode mit Durchschnitt
- Pro-Periode-Berechnung (Monat oder Jahr)

**Mehrjahres:**
- Sammelt Daten für jedes Jahr
- Berechnet Jahr-zu-Jahr Änderungen
- Ermittelt Gesamtdurchschnitte

**Quartals:**
- Q1: Jan-März, Q2: Apr-Juni, Q3: Juli-Sept, Q4: Okt-Dez
- Berechnet Quartal-zu-Quartal Änderungen
- Optional: Vergleich mit Vorjahresquartalen

### Performance
- Alle Berechnungen erfolgen serverseitig
- Effiziente SQL-Abfragen
- Caching durch Frontend-State-Management

## 📝 Weitere Verbesserungen

Mögliche zukünftige Erweiterungen:
- Export-Funktionen für Berichte
- Benachrichtigungen bei großen Abweichungen
- Budgetvergleiche mit Benchmark
- Personalisierte Empfehlungen basierend auf Trends
- Multi-Account Benchmarks (anonymisierte Durchschnitte)
