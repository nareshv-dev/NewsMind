# Verification status

Verified locally on Windows with Python 3.12.4, Node 24.18.0, SQLite, and Next.js 16.3.5.

| Check | Result |
| --- | --- |
| Alembic upgrade and explicit demo seed | Passed; 16 fictional fixtures |
| Backend tests | 12 passed |
| TypeScript | Passed, independently and in production build |
| ESLint | Passed |
| Next.js production build | Passed |
| Chromium desktop/mobile browser tests | 4 passed |
| Light/dark desktop and mobile screenshots | Captured and inspected |
| Public browsing without credentials or login | Verified |
| API errors do not become demo feeds | Verified |
| Expired news hidden before cleanup; bookmarks cascade on deletion | Verified in backend tests |
| Bounded provider backoff and AI fallback | Verified with mocked upstream failures |
| Signed JWT validation, expiry/audience rejection, account ownership | Verified with generated test keys and dependency overrides |

Browser checks used 1440x1000 desktop and 390x844 mobile viewports. They exercised lead images, detail navigation, categories, search, regional filters, empty results, pagination URL state, theme persistence through reload, unavailable accounts, and explicit API failure states. No page errors were captured. Screenshots are in ignored `test-results/`.

Live NewsAPI fetching, OpenAI calls, and Supabase email sign-in were not exercised: no project credentials were configured. PostgreSQL/Compose was not exercised because Docker Desktop's engine was unavailable. The PostgreSQL schema, search index and advisory lock are implemented but require a PostgreSQL run before deployment. Backend tests report one dependency deprecation warning from Starlette's use of an AnyIO portal alias; tests pass.

The first build encountered sandbox subprocess restrictions; it passed with normal subprocess access. Initial browser tests exposed filter-state/locator and cold-route timing issues; the final run passed after fixes. No public deployment or production-readiness claim is made.

## Free live RSS integration

Nine publisher RSS feeds were successfully fetched from the local machine. Initial ingestion fetched 410 entries and stored 323 articles after duplicate/invalid/expired records were skipped. All seven categories contain live articles. 313 retained live articles included publisher-supplied image references. The local `.env` now enables live RSS; hourly fetching and five-minute deletion continue through the worker. Demo fixtures remain stored separately and are excluded from live public endpoints.

RSS parsing tests cover markup removal, attribution, publication dates, media fields, topic/geography separation, deduplication, empty/invalid feeds, unknown feed IDs, and expired incoming entries. Existing provider/expiry/authentication tests continue to pass. Live browser checks live in `frontend/tests/live.spec.ts`; fictional-fixture tests skip in live mode, and the live suite skips in demo mode.

Final live browser verification: 2 passed against the built frontend on port 3000, with desktop (1440x1000) and mobile (390x844) coverage. Verified real headlines, no demo banner, publisher images, original-source attribution, article navigation, Tamilnadu browsing, source filters, pagination, light/dark themes, and no page errors. ESLint passed. Screenshots: `test-results/*-live-light.png` and `test-results/*-live-dark.png`. Earlier development-server checks encountered a connection reset and navigation delays; the built frontend passed both flows in 5.8 seconds total and is left running locally. A second RSS ingestion stored zero duplicates (410 skipped unchanged entries).
