```markdown
**TL;DR**
- Kurzer, priorisierter Überblick über das Frontend (oberste Ebene).
- Fokus: Projekt- / Build-Setup, Abhängigkeiten, offensichtliche Risiken (Repo-Größe, Secrets, Build-ops), schnelle Verbesserungen.

Scope
- Dateien/Ordner, die ich auf oberster Ebene gelesen habe: `package.json`, `index.html`, `vite.config.js`, `Dockerfile`, `nginx.conf`, `.env`, `node_modules/`, `public/`, `src/`.

Schnelle Beobachtungen
- Tech-Stack: React (v19), Vite (v7), TailwindCSS, Zustand (state), Recharts (charts), Axios for API calls. Test-Stack: Vitest + Testing Library.
- Projekttyp: offenbar JavaScript/JSX app (`src/main.jsx`) — es gibt `@types/react` in `devDependencies` (Typings vorhanden, eventuell Teilweiser TS-Migration).
- Lockfile: `package-lock.json` vorhanden — deterministischer installierbarer Zustand vorhanden.
- `node_modules/` ist im Arbeitsverzeichnis vorhanden (Liste zeigte `node_modules/`). Prüfen, ob das versehentlich committed ist — das erhöht Repo-Size stark.
- `.env` vorhanden im `frontend/` Verzeichnis — bitte prüfen, ob sensible Keys enthalten sind und ob `.gitignore` korrekt konfiguriert.

Immediate Risks (P0)
- Secrets in repo: Wenn `.env` Commit-Historie enthält oder sensible Keys stehen, ist das sofortig kritisch; prüfen und rotieren falls nötig.
- Large repository size: `node_modules/` sollte nicht im VCS liegen. Entfernen + `.gitignore` vermeiden unnötige bloat.
- API env/config mismatch: Stelle sicher, dass die Frontend-API-URL-Konfiguration kompatibel ist mit Backend CORS und Deployment (env-varianten: dev/prod).

High-level Findings / Recommendations
- Dependency & Tooling
  - `package.json` zeigt moderne libs; empfehle regelmäßigen Dependabot-like checks and `npm audit` in CI.
  - Nutze lockfile (`package-lock.json`) in CI for reproducible builds; consider `pnpm`/`yarn` if monorepo or disk space is a concern.

- Build & Deploy
  - `vite.config.js` is minimal. Add explicit `base` (if app is served from subpath), build optimizations (chunking) and asset hashing if needed.
  - `Dockerfile` + `nginx.conf` exist — verify that CI builds artifact and nginx serves from the correct built `dist/` path. Add a small multi-stage build if not already present.

- Code Health & DX
  - Lint and tests are already scripted (`lint`, `test`, `test:coverage`). Add CI pipeline to run them on PRs.
  - Consider adding type-checking (`tsc --noEmit`) or enabling stricter ESLint rules to catch runtime errors early.

- Performance & Assets
  - Optimize images in `public/` (webp/AVIF), set proper cache headers in `nginx.conf`.
  - Use lazy-loading for heavy visualizations (Recharts) and code-splitting for route-based components.

Low-effort Quick Wins
- Remove `node_modules/` from repository and ensure `.gitignore` includes it.
- Ensure `.env` is not tracked (add example `.env.example`) and document required env vars in `README` or `frontend/README.md`.
- Add a CI job that runs `npm ci`, `npm run lint`, `npm test -- --coverage`, and `npm run build`.

Next step (proposed)
- Ich kann jetzt detailliert das `frontend/src/` Verzeichnis scannen und ein `08_frontend_overview.md` erweitern zu `09_frontend_src.md` mit component- & route-level Analysen. Soll ich fortfahren und direkt die `src/`-Analyse starten, oder möchtest du zuerst dieses Top-Level-Overview prüfen? (Sag `weiter` um mit `src/` fortzufahren.)

Files referenced
- `frontend/package.json`
- `frontend/index.html`
- `frontend/vite.config.js`
- `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.env` (prüfen auf Secrets)

Integration & Cross-References
- **Related frontend audits:** see `/audit/09_frontend_src.md`, `/audit/10_frontend_hooks_services.md`, `/audit/11_frontend_pages.md`, and `/audit/12_frontend_components.md` for detailed component- and call-site mappings.
- **Related backend audits:** cross-check `audit/06_backend_routers_endpoints.md`, `audit/05_backend_services.md`, and `audit/04_backend_schemas.md` before changing API shapes.
- **Concrete integration notes:**
  - The frontend uses `import.meta.env.VITE_API_URL` (default `/api/v1`) — ensure all backend endpoint docs include the API base path.
  - Key cross-cutting areas: CSV import (preview/import), recategorization jobs, transfers detection and deletion jobs — these appear in both frontend and backend audits and must have a coordinated async/sync contract.
- **Suggested immediate task:** create a small `/audit/README.md` index linking frontend and backend audit files and listing the top 5 cross-service contracts to reconcile (CSV import, money serialization, recategorize job, transfers detect, paginated list shapes).

```