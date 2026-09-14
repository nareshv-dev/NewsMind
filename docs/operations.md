# Operations

From `backend/`, `python -m app.workers.run loop` is the separately runnable scheduler. Keep it alive with a service manager or the Compose worker. It fetches hourly and performs cleanup every five minutes. For an external scheduler, run `python -m app.workers.run once` hourly and `python -m app.workers.run cleanup` every five minutes; do not also schedule a loop. On Windows, use Task Scheduler with the absolute `.venv\Scripts\python.exe` path, these arguments, and `backend/` as the Start in directory.

The current local configuration uses `DEMO_MODE=false` and `NEWS_PROVIDER=rss`, which needs no provider API key. To return to fixtures, set `DEMO_MODE=true` and restart the API/worker. To select NewsAPI, set `NEWS_PROVIDER=newsapi` with server-side credentials. `RSS_FEEDS` selects registered publisher feeds; unknown IDs fail explicitly. The current RSS sources are intended for local personal evaluation and are subject to publisher reuse terms. Use `NEWS_QUERIES` only for NewsAPI; RSS selects feeds rather than arbitrary keyword searches.

PostgreSQL advisory locks prevent concurrent ingestion workers across processes/hosts using the same database. SQLite uses an exclusive `.ingestion.lock` file. After a crashed SQLite worker, confirm no worker is active and remove that file before restarting. PostgreSQL releases its lock when its connection closes. SQLite is intended for a single-machine development workflow.

Set a random server-only `OPS_TOKEN`. Query counts and sanitized upstream failures:

```powershell
$headers = @{Authorization = "Bearer $env:OPS_TOKEN"}
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ops/runs -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

No anonymous endpoint starts ingestion. Health exposes basic configuration booleans and latest run state, never keys. Workers do not log payloads or private credentials. Disable HTTP access logs (`--no-access-log`) when running locally or configure request-log redaction in deployment. Monitor failures, provider quotas, worker availability, database disk usage and backup retention before deployment.

The original hardcoded provider credential in `app.py` has been removed; the prototype now reads `NEWSAPI_KEY` from the environment. The credential remains in earlier Git history, so rotate it with the provider. History cleanup requires a separately coordinated rewrite. `.env.example` files contain no secrets. The new platform has no default operational token or provider credentials.

Current limitations: capped upstream results, no provider licensing enforcement automation, no full-text article downloads, no semantic clustering, no automatic feed personalization, no reading history, no distributed limiter, no deployment/monitoring infrastructure. PostgreSQL, live NewsAPI, OpenAI, and Supabase should each be exercised with authorized credentials before treating those integrations as validated.
