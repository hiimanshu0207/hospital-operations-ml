# Day 01 — Project Setup & Scaffold

**Date:** 2026-10-23 (Friday)
**Day:** 1 of 15

---

## Today's Objective

Set up the complete monorepo structure with a working React + Vite frontend
and FastAPI backend, verify both applications start successfully, and establish
all project documentation.

---

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Workspace and runtime inspection | ✅ Done |
| 2 | Prerequisite check (Node, npm, Python, pip, Git) | ✅ Done |
| 3 | Created monorepo folder structure | ✅ Done |
| 4 | Scaffolded React + Vite + Tailwind CSS frontend | ✅ Done |
| 5 | Scaffolded FastAPI backend with `/health` endpoint | ✅ Done |
| 6 | Installed all npm dependencies (recharts, axios, react-router-dom) | ✅ Done |
| 7 | Installed Tailwind CSS with Vite plugin | ✅ Done |
| 8 | Created Python virtual environment and installed pip dependencies | ✅ Done |
| 9 | Configured `.gitignore` | ✅ Done |
| 10 | Created `.env.example` files (root + backend) | ✅ Done |
| 11 | Created documentation (README, PROJECT_PLAN, ARCHITECTURE) | ✅ Done |
| 12 | Created test file for `/health` endpoint | ✅ Done |
| 13 | Verified frontend build (`vite build`) | ✅ Passed — 16 modules, built in 297ms |
| 14 | Verified backend health endpoint (`pytest`) | ✅ 2/2 tests passed |
| 15 | Git initialization and initial commit | ⏳ Pending (Git not installed) |

---

## Files Created

### Root
- `.gitignore`
- `.env.example`
- `README.md`
- `PROJECT_PLAN.md`

### Frontend (`frontend/`)
- `index.html` (updated title + meta)
- `vite.config.js` (Tailwind + API proxy)
- `src/index.css` (Tailwind import)
- `src/App.jsx` (landing page with health check)
- `src/main.jsx` (entry point — Vite default)
- `src/services/api.js` (axios client)
- `src/components/.gitkeep`
- `src/pages/.gitkeep`
- `src/hooks/.gitkeep`
- `src/utils/.gitkeep`
- `package.json` (with all dependencies)

### Backend (`backend/`)
- `app/__init__.py`
- `app/main.py` (FastAPI + `/health`)
- `app/config.py` (pydantic-settings)
- `app/database.py` (SQLAlchemy + SQLite)
- `app/models/__init__.py`
- `app/schemas/__init__.py`
- `app/routers/__init__.py`
- `app/services/__init__.py`
- `requirements.txt`
- `.env.example`

### ML & Data
- `ml/__init__.py`
- `ml/README.md`
- `data/README.md`

### Tests
- `tests/__init__.py`
- `tests/test_backend/__init__.py`
- `tests/test_backend/test_health.py`
- `tests/test_ml/__init__.py`

### Documentation
- `docs/ARCHITECTURE.md`
- `DAILY_REPORTS/day-01.md` (this file)

---

## Commands Executed

```
node --version          → v24.22.1
npm --version           → 11.19.1
python --version        → Python 3.15.1
pip --version           → pip 26.2.2
git --version           → NOT FOUND

npm create vite@latest ./frontend -- --template react   → ✅ Success
npm install                                              → ✅ 24 packages
npm install recharts axios react-router-dom              → ✅ 70 packages
npm install -D tailwindcss @tailwindcss/vite             → ✅ 17 packages
vite build (via node direct invocation)                  → ✅ 16 modules, dist/ created

python -m venv venv                                      → ✅ Created
pip install -r requirements.txt                          → ✅ 38 packages installed
pytest tests/test_backend/test_health.py                 → ✅ 2 passed in 2.40s
```

---

## Tests & Results

| Test | Expected | Actual |
|------|----------|--------|
| `vite build` | Exit code 0, `dist/` created | ✅ Exit 0 — 16 modules, 3 output files |
| `GET /health` | `{"status": "healthy"}` | ✅ Verified via pytest TestClient |
| `pytest test_health.py` | 2 tests pass | ✅ 2 passed in 2.40s |

> **Note:** `npm run build` fails due to `&` in the workspace path breaking npm script
> resolution. Use `node node_modules/vite/bin/vite.js build` as a workaround.
> This is a known Node.js issue with special characters in directory names.

---

## Known Issues & Blockers

| Issue | Severity | Resolution |
|-------|----------|------------|
| **Git not installed** | 🔴 High | Install via `winget install --id Git.Git -e --source winget`, then restart terminal |
| **`&` in workspace path** | 🟡 Medium | `npm run build` / `npm run dev` fail because Node.js splits the path at `&`. Workaround: invoke vite binary directly with `node node_modules/vite/bin/vite.js build` or `node node_modules/vite/bin/vite.js` for dev server. Long-term fix: rename workspace folder to avoid `&`. |

---

## Next Day's Tasks (Day 2)

1. Install Git and initialize repository
2. Initial commit with all scaffolding files
3. Configure GitHub remote and push
4. Design hospital domain entities (patients, departments, beds, staff)
5. Create SQLAlchemy ORM models
6. Build synthetic data generator script
7. Create CRUD API endpoints for core entities
8. Frontend: basic navigation layout with react-router-dom
