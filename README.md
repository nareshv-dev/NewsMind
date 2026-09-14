# NewsMind

An editorial news reader with a Next.js frontend, FastAPI API, SQLAlchemy persistence, and a separate ingestion/retention worker. The original Streamlit prototype remains in `app.py`; the new application lives in `frontend/` and `backend/`.

## Local demo (PowerShell, Python 3.12+, Node 20.9+)

From `E:\Naresh_Projects\NewsMind`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.workers.seed
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In a second terminal:

```powershell
Set-Location E:\Naresh_Projects\NewsMind\frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000. API documentation: http://127.0.0.1:8000/docs. SQLite provides a no-Docker local fallback; production configuration should use PostgreSQL. Demo mode is explicit and contains fictional examples, with illustrative Unsplash photography, rather than fabricated real news. The seed command is idempotent and preserves existing data. To refresh expired fixtures, run cleanup then seed again.

For the exact tested Python dependency set, use `backend/requirements.lock.txt` instead of `backend/requirements.txt`. The frontend includes `package-lock.json`; use `npm ci` for locked installs. Rerunning seed updates fixture image references but preserves content and publication timestamps. The lead photo is [Marina Beach, Chennai by Nico Smit](https://unsplash.com/photos/a-group-of-boats-sitting-on-top-of-a-sandy-beach-a5L5xTmapHA), used under the Unsplash License; it illustrates the place, not the fictional event.

## PostgreSQL with Docker

Start Docker Desktop. Copy `.env.example` to `.env`, add a strong `POSTGRES_PASSWORD` (URL-safe characters), then:

```powershell
docker compose up --build -d
docker compose exec api python -m app.workers.seed
```

Run the frontend separately as above. API and PostgreSQL ports bind only to localhost. Compose substitutes the PostgreSQL connection URL for the API and worker. The worker runs cleanup in demo mode but never fetches live news. Stop using `docker compose down` (without `-v` to preserve the database).

## Live providers and AI

Free live news is supported through publisher RSS feeds without API credentials. Set `DEMO_MODE=false` and `NEWS_PROVIDER=rss`, restart the API and worker, and run `python -m app.workers.run once` from `backend/`. The default registry includes NDTV.com India/world/sports, Gadgets 360, The Hindu Tamilnadu, and BBC world/sports/technology/politics. `RSS_FEEDS` selects pipe-separated registry IDs. Stories are fetched hourly and retain their actual publication timestamps. Missing, future, and expired timestamps are rejected. RSS provides a current feed snapshot, not a guaranteed complete four-day backfill; retained coverage grows with regular fetching.

The current local instance runs the built frontend (`npm run build` then `npm start`), which avoids development compilation delays. Use `npm run dev` instead when editing the UI; stop the existing frontend process first or choose another port. Verify live browsing with `npx playwright test tests/live.spec.ts --workers=1`. The default test command skips suites that do not match the configured demo/live mode.

These feeds are for local personal evaluation, subject to publisher terms and availability. [NDTV RSS terms](https://www.ndtv.com/rss?site=classic) permit personal, non-commercial use with NDTV.com attribution. [BBC feed guidance](https://www.bbc.co.uk/sport/articles/cqllxj2n4kyo) links its reuse terms. RSS availability does not grant unrestricted commercial redistribution rights; review publisher licensing before public deployment. The implementation stores supplied metadata/excerpts only and never scrapes full article bodies. Topic and geography hints from dedicated feeds are labeled `feed+heuristic`, not AI analysis.

For NewsAPI instead, set `DEMO_MODE=false`, `NEWS_PROVIDER=newsapi`, and supply `NEWSAPI_KEY`. Demo fixtures are excluded from live endpoints. NewsAPI plan/source licensing must permit the intended use. The frontend never receives news or AI keys. Run from `backend/`:

```powershell
..\.venv\Scripts\python.exe -m app.workers.run once
..\.venv\Scripts\python.exe -m app.workers.run loop
```

The loop fetches hourly and deletes expired articles every five minutes. `NEWS_QUERIES` can override the pipe-separated regional/topic queries. Each query fetches up to 100 recent articles, so this initial implementation is not exhaustive archival ingestion. Backoff and retries are bounded. Failed requests are recorded as failures, distinct from successful empty results. No live request silently receives demo data.

For optional AI set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and `AI_MODEL=gpt-5-mini` (or another structured-output model available to your account). SDK `responses.parse` validates a Pydantic schema. AI errors, refusals, absent credentials, or short descriptions use a labeled heuristic classifier and source excerpt. Model output is not independently fact-checked; original reporting remains authoritative. See [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) and [GPT-5 mini](https://developers.openai.com/api/docs/models/gpt-5-mini). Embeddings are intentionally omitted; PostgreSQL full-text search handles initial search.

## Optional accounts

Supabase handles secure email magic-link authentication; no passwords are implemented here. Create a Supabase project, enable email auth, configure the site URL and redirect allowlist (`http://127.0.0.1:3000/account`), and use **asymmetric JWT signing keys (ES256 or RS256)**. Set `SUPABASE_URL` in the server `.env`. Copy `frontend/.env.example` to `frontend/.env.local` and set the public URL and anon/publishable key, then restart the frontend. Never use the service-role key in the browser. The backend validates signature, issuer, audience, expiry, and user ID using JWKS. Bookmarks and preferences are scoped to the verified user. Unconfigured account integrations remain visibly unavailable. Followed categories and preferred language/region are stored; automatic feed personalization and reading history are not enabled yet.

## Verification

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest tests -q
Set-Location ../frontend
npm run typecheck
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests require the seeded API and frontend running on ports 8000/3000. They cover desktop/mobile public browsing, images, navigation, search/filtering, pagination, theme persistence, unavailable accounts, and API errors. Backend tests cover deduplication, validation, expiry boundaries and deletion cascades, classification fallback, failed/empty ingestion, and ownership. Live integrations require credentials and separate verification.

See [architecture](docs/architecture.md), [operations](docs/operations.md), and [verification status](docs/verification.md). No public deployment is included.
