<div align="center">

# 🌾 KisanProfit — Farmer Expense & Profit Tracker

**Know Your Cost. Track Your Crop. Grow Your Profit.**

[![tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)](#quick-start) [![live](https://img.shields.io/badge/%E2%96%B6_live_demo-kisanprofit--web.onrender.com-2ea44f)](https://kisanprofit-web.onrender.com) [![i18n](https://img.shields.io/badge/i18n-EN%20%2F%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80%20%2F%20%E0%A4%AE%E0%A4%B0%E0%A4%BE%E0%A4%A0%E0%A5%80-blue)](#-features) [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](backend/) [![React 18](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](frontend/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](backend/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

KisanProfit is a production-quality, hackathon-ready web platform that helps farmers track farm expenses, record harvest and sales, and see their **real profit per crop** — with AI insights, a profit simulator, weather advisories, market reference prices, PDF/CSV reports, and full **English / हिन्दी / मराठी** support.

**▶ Try it live: [kisanprofit-web.onrender.com](https://kisanprofit-web.onrender.com)** — demo login: mobile `9999999999`, password `demo1234` (pre-seeded demo farm, **read-only** so its numbers never drift). Free-tier hosting: the first request after ~15 min idle takes ~30–50 s to wake.

Built for farmers, not bankers: big readable numbers, large touch targets, 10-second expense entry (with **voice input**), bottom-sheet forms on mobile, and honest empty/error/loading states.

---

> ✅ **Repository status** — KisanProfit is a **complete, working, deployed application**: FastAPI + SQLAlchemy backend (72 passing tests), React 18 + TypeScript + Tailwind v4 frontend, live on Render (frontend static site + FastAPI service) with a managed Postgres. Locally, the same stack runs via Docker Compose with a pre-seeded demo farm. The README below is the original feature specification the implementation follows — the architecture tree and demo numbers are verified against the running app.

---

## ✨ Features

| Module | Highlights |
|---|---|
| **Dashboard** | Total investment, revenue, profit, ROI; active crops, farms, upcoming harvest, pending sales; 5 charts; date filters (this month / 3 months / season / year / all); AI summary banner |
| **Farms & Crops** | Multiple farms; crop cards with days-since-sowing, current expense, expected revenue/profit; crop lifecycle timeline (sowing → expense → harvest → sale → profit) |
| **Expense Tracker** | 12 categories, quick-add buttons, voice entry with **manual confirmation**, search, crop/category/date filters, sort by amount/date, stats (total, this month, largest category, average) |
| **Production** | Harvest records, expected vs actual comparison ("8.3% below expected production") |
| **Sales** | Quantity × price, transport & other charges → gross & net revenue (computed server-side) |
| **Profit Engine** | Backend-only financial math: total cost, revenue, profit, ROI, cost/profit per acre, cost per quintal, break-even price, production variance — all zero-safe |
| **Profit Simulator** | Try any price; 4 price points, what-if scenarios (price +10%, production −15%, costs +20%), break-even highlight |
| **Crop Comparison** | Side-by-side metrics with best performer highlighted |
| **Kisan AI** | Chat in English/Hindi/Marathi answered from *your own data* — never invents figures; voice input; deterministic offline engine by default, Google Gemini or OpenAI when a key is added |
| **AI Insights** | Deterministic insights: top expense category share, production variance, break-even margin; honest "not enough data" messaging |
| **Weather** | Live 7-day forecast (Open-Meteo, keyless), rain advisories, graceful offline handling; uses the pinned farm location |
| **Map & Location** | OpenStreetMap map on each farm + tap/drag location picker; Nominatim geocoding (Find on map) with offline fallback |
| **Receipt OCR** | Scan a receipt photo to prefill an expense (never auto-saved — always confirm); Google Gemini vision, demo mode without a key |
| **Market Prices** | Live data.gov.in mandi prices when an API key is added; otherwise clearly-labeled reference prices with source + date; price revenue simulator |
| **Reports** | Crop profitability PDF, summary PDFs (expense/sales/monthly/seasonal/annual), CSV exports |
| **Notifications** | Harvest/high-expense alerts with per-type toggles |
| **i18n** | Full app in English, हिन्दी, मराठी (nav, forms, dashboards, categories, errors, empty states) |
| **Voice** | Web Speech API for expense entry + AI chat; spoken amounts always require confirmation |

## 🏗️ Architecture

```
kisanprofit/
├── backend/                 # FastAPI + SQLAlchemy (Python 3.10+)
│   ├── app/
│   │   ├── main.py          # app factory, CORS, lifespan (seed + reminders)
│   │   ├── core/            # config (env), security (bcrypt + JWT)
│   │   ├── models/          # users, farms, crops, expenses, production, sales,
│   │   │                    #   notifications, market_prices, weather_cache, ai_conversations
│   │   ├── schemas/         # Pydantic validation (all inputs validated)
│   │   ├── api/             # REST routers: auth, farms, crops, expenses, production,
│   │   │                    #   sales, analytics, ai, weather, market, reports, notifications,
│   │   │                    #   location (geocode), ocr (receipt), integrations (status)
│   │   ├── services/        # finance.py = the calculation engine (all money math)
│   │   │                    #   insights.py, ai_service.py, notifications.py
│   │   ├── ai/              # provider abstraction (offline | gemini | openai | auto)
│   │   ├── location/        # OpenStreetMap Nominatim geocoding + offline fallback
│   │   ├── ocr/             # receipt OCR (Gemini vision; labeled demo mode w/o key)
│   │   ├── weather/         # Open-Meteo with DB cache + graceful fallback
│   │   ├── market/          # live data.gov.in mandi prices; reference fallback
│   │   ├── reports/         # PDF (fpdf2) + CSV generation
│   │   └── seed.py          # demo farmer (is_demo=True, separate from real users)
│   └── tests/               # 53 pytest tests (auth, CRUD, finance math, edge cases, authz, integrations)
└── frontend/                # Vite + React 18 + TypeScript + Tailwind v4
    └── src/
        ├── pages/           # Landing, auth, dashboard, farms, crops, expenses,
        │                    #   production, sales, simulator, compare, analytics,
        │                    #   ai, insights, weather, market, reports, notifications, settings
        ├── components/      # UI kit (Button/Card/Modal/BottomSheet/…), charts (Recharts),
        │                    #   MapView (Leaflet + OpenStreetMap), layout (sidebar + bottom nav + FAB)
        ├── contexts/        # Auth (JWT), i18n, toasts
        ├── hooks/           # useApi (loading/error/refresh), useVoice
        └── i18n/            # en / hi / mr dictionaries
```

**Key rules honored:**
- All financial calculations happen in the backend (`services/finance.py`). The frontend only formats and displays.
- AI insights are computed deterministically from real data; an LLM may rephrase but never invent figures.
- Every API is JWT-protected; farmers can only access their own records (verified by tests).
- Secrets (SECRET_KEY, AI keys) live in backend environment variables only.

## 🚀 Quick Start

### Backend (port 8000)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional — defaults work out of the box
uvicorn app.main:app --reload --port 8000
```

Demo data (farmer with cotton/soybean/wheat, ₹80k expenses, sales, production, notifications) is seeded automatically. API docs: `http://127.0.0.1:8000/docs`.

### External services & API keys

Everything runs in **clearly-labeled mock/demo mode** until a key is added — no broken screens, ever.
Keys live in `backend/.env` only (see `backend/.env.example`), and live/demo status is visible in the app under **Settings → Connected Services**.

| Feature | Provider | Key? | Env var | Without a key |
|---|---|---|---|---|
| Weather | Open-Meteo | No | — | Always live when online |
| Map + location search | OpenStreetMap / Nominatim | No | `NOMINATIM_EMAIL` (recommended) | Live; offline lookup fallback |
| Mandi prices | data.gov.in | Yes | `DATA_GOV_IN_API_KEY` | Clearly-labeled reference prices |
| Kisan AI assistant | Google Gemini | Yes | `GEMINI_API_KEY` (+ `AI_PROVIDER=auto`) | Deterministic engine on your own records |
| Receipt OCR | Google Gemini (vision) | Yes | `GEMINI_API_KEY` | Labeled demo scan — results always need your confirmation |

Add keys to `backend/.env`, restart the backend, and the same endpoints switch to live data automatically.

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` to the backend automatically.

### Using VS Code Live Server instead (static hosting)

The repo root contains an `index.html` that redirects to the built app, so opening
**http://localhost:5500** shows KisanProfit instead of the folder listing. The app uses
hash-based routing and relative asset paths, so it works from any static server:

```bash
cd frontend
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run build   # point the bundle at the backend
```

Then open `http://localhost:5500` (or `.../frontend/dist/`). The backend already allows
CORS from `localhost:5500` / `127.0.0.1:5500`. Omit `VITE_API_BASE_URL` when deploying
behind a reverse proxy that forwards `/api` (like the bundled nginx setup).

### Run tests

```bash
cd backend && .venv/bin/python -m pytest tests/ -q      # 72 tests
cd frontend && npm run build                             # tsc + vite production build
```

## 🎪 Demo (for judges — 60 seconds)

1. Open http://localhost:5173 → **Create Account** or **Explore Demo Farm**
2. **Dashboard** — AI summary, profit ₹85,400, ROI 106.75%, all charts live
3. Open **Cotton** crop → full snapshot + lifecycle timeline
4. **Expenses** → stats, search/filter/sort, quick-add buttons, 🎙 voice entry, 📷 receipt scan
5. The shared demo farm is **read-only** (no Add button), so the figures stay exactly as documented — ₹80,000 across 14 entries. **Create Account** to run this step for real and watch the totals update
6. **Profit Simulator** → load Cotton → change price ₹7,000 → ₹7,500 → profit ₹36,400 → ₹51,400
7. **Kisan AI** → ask *"Where am I spending the most?"* (or in Hindi/Marathi)
8. **Weather** → live forecast + rain advisories for Akola
9. **Reports** → download the Cotton PDF report
10. Try the language switcher (हिन्दी / मराठी) — the whole app translates

Demo login: mobile **9999999999** / password **demo1234** (or one-tap "Explore Demo Farm").

> 🔒 The demo account is read-only on purpose: every mutating API route rejects it with
> `403`, so a public visitor can browse the whole app but cannot pollute or delete the
> farm a judge is about to look at. A nightly workflow re-seeds it as a safety net, and
> the in-app banner tells visitors to create their own account to record real data.

## 🔒 Security

- bcrypt password hashing; JWT access tokens (7-day, configurable)
- All endpoints require auth via bearer token; per-user data scoping on every query
- Pydantic validation on all inputs (negative amounts, wrong categories, foreign crop ids rejected)
- CORS allow-list from env; no secrets in the frontend bundle
- The shared demo account is **read-only** — all farm-data writes (`farms`, `crops`,
  `expenses`, `production`, `sales`) are rejected for `is_demo` users, and a fail-closed
  test asserts no mutating route can be added without the guard
- The nightly demo reset is a token-guarded admin route (`POST /api/admin/reseed-demo`);
  it 404s unless `RESEED_TOKEN` is configured, and the token is never in the repo
- Rate limiting is ready to add behind a reverse proxy (documented in deployment)

## 🐳 Deployment (production)

PostgreSQL is supported via `DATABASE_URL` (SQLite is the default for zero-setup runs):

```bash
# example backend env for Postgres
DATABASE_URL=postgresql+psycopg://kisan:pass@db:5432/kisanprofit
CORS_ORIGINS=https://app.yourdomain.com
SECRET_KEY=<random 64-hex string>
AI_PROVIDER=auto             # gemini/openai/offline — see .env.example
SEED_DEMO_DATA=true          # seed the demo farm at startup
RESEED_TOKEN=<random hex>    # enables the nightly demo reset route; unset = disabled
GEMINI_API_KEY=<your key>    # optional: enables AI + receipt OCR
DATA_GOV_IN_API_KEY=<key>    # optional: live mandi prices
```

Frontend production build: `cd frontend && npm run build` (static files in `dist/`). Serve with any static host/CDN; point it at the API origin. Use `docker compose` for the full stack (see `docker-compose.yml`).

## 📜 License

Released under the [MIT License](LICENSE) — built as a hackathon project, free for farmers.