# Architecture

## Overview

The system ingests MoMo SMS messages from a raw XML export, runs them through a four-stage ETL pipeline (parse → clean → categorize → load), and persists the results to a local SQLite database. Pre-aggregated analytics are exported to a static JSON file and rendered by a lightweight browser frontend, with an optional FastAPI layer available when live querying is required. The pipeline is designed for idempotency — re-running against the same or overlapping exports is safe — and uses a dead-letter pattern to absorb malformed records without aborting the batch.

## Components

### Raw XML Input

**Responsibility:** Provides the source dataset: a UTF-8 encoded XML file containing one `<sms>` element per MoMo SMS message, stored at `data/raw/momo.xml`. **Tech:** lxml preferred; ElementTree (stdlib) used as a fallback when lxml is unavailable. **Rationale:** Keeping the raw file unmodified preserves the original export for auditing and replay. Separating the input artifact from the parsing step means the file can be replaced with a newer export without touching any pipeline code.

### parse_xml.py

**Responsibility:** Deserializes `data/raw/momo.xml` into a list of Python dicts, extracting the `body`, `date`, `address`, and `type` fields from each `<sms>` element. **Tech:** lxml or ElementTree. **Rationale:** Isolating XML deserialization into a single module means any schema change in the upstream export only requires updating this file. Downstream stages receive plain Python dicts and are entirely decoupled from the XML format.

### clean_normalize.py

**Responsibility:** Sanitizes and normalizes the raw parsed dicts — converting date strings to ISO-8601, normalizing phone numbers to E.164 format, and parsing amount strings to `Decimal` values. **Tech:** Pure Python with `re` for regex-based extraction and the stdlib `decimal` module. **Rationale:** Separating cleaning from parsing keeps each module independently testable with simple dict fixtures. Normalization at this stage guarantees that all downstream modules work with a consistent, typed representation.

### categorize.py

**Responsibility:** Classifies each normalized record into one of the transaction categories (`incoming`, `outgoing`, `payment`, `airtime`, `unknown`) by adding a `category` key to the dict. **Tech:** Rule-based keyword matching against the `body` field. **Rationale:** Rule-based classification is deterministic and fully auditable — the mapping between keywords and categories is readable code, not an opaque model artifact. This removes any ML runtime dependency and makes it straightforward to add or adjust categories as new SMS templates emerge.

### load_db.py

**Responsibility:** Upserts categorized records into the `transactions` table in `data/db.sqlite3` and writes pre-aggregated analytics to `data/processed/dashboard.json`. **Tech:** Python `sqlite3` stdlib for database access; `json` stdlib for the JSON export. **Rationale:** Idempotency is enforced by hashing the raw SMS `body` with SHA-256 and storing the result in a `hash` column with a `UNIQUE` constraint; duplicate rows are silently ignored on re-run. Generating `dashboard.json` at load time keeps the static frontend fast without requiring a live server.

### SQLite (data/db.sqlite3)

**Responsibility:** Durable persistence layer for all transaction records. **Tech:** SQLite via the Python `sqlite3` stdlib — no external database process required. **Rationale:** SQLite is zero-configuration, entirely file-based, and trivially portable, which suits a week-1 dataset and a team working across different machines. The file can be committed to a demo branch for quick sharing and replaced with a Postgres connection string later without changing any ETL logic.

### dashboard.json (data/processed/dashboard.json)

**Responsibility:** A pre-aggregated snapshot of analytics data — total transaction count, breakdowns by category and month, and top contacts — consumed by the static frontend on page load. **Tech:** UTF-8 encoded JSON. **Rationale:** Generating the aggregates at pipeline time eliminates the need for a live API call when the page opens, making the default deployment fully static. The file is regenerated on each pipeline run, so it stays consistent with the database without requiring a caching layer.

### Static Frontend

**Responsibility:** Renders charts and transaction summaries in the browser using data loaded from `dashboard.json`. **Tech:** Vanilla HTML (`index.html`), CSS (`web/styles.css`), and JavaScript (`web/chart_handler.js`) — no SPA framework. **Rationale:** Avoiding a framework eliminates the Node.js build step entirely, keeping the repository lightweight and deployable from any plain file server or static hosting service. This also lowers the onboarding barrier for teammates whose primary focus is the data pipeline rather than frontend tooling.

### FastAPI (optional)

**Responsibility:** Provides live query endpoints (`/transactions`, `/analytics`) when real-time filtering or pagination over the SQLite database is needed. **Tech:** FastAPI with Uvicorn. **Rationale:** The static frontend works without this component; FastAPI is an opt-in overlay enabled only when dynamic querying justifies running an additional process. Keeping it optional means the default setup has no Python web server dependency and no port to manage.

### Dead Letter (data/logs/dead_letter/)

**Responsibility:** Captures records that fail any ETL stage — parse errors, normalization failures, schema violations — as individual JSON files so they can be inspected and replayed without blocking the rest of the batch. **Tech:** One JSON file per failed record, named by a timestamp and partial hash. **Rationale:** A fail-safe approach is preferable to fail-fast here: a single malformed SMS in a large export should not abort the entire run. Dead-lettered records can be corrected and fed back into the pipeline independently.

### ETL Log (data/logs/etl.log)

**Responsibility:** Structured run log capturing stage entry/exit timings, record counts at each stage boundary, and error summaries. **Tech:** Python `logging` stdlib configured with a file handler and a structured format. **Rationale:** Structured log output enables post-run auditing without parsing free-form text. CI pipelines can assert on log content (e.g., zero records dead-lettered, all stages completed) to gate on pipeline health.

## Data Flow

1. **Raw XML** → `data/raw/momo.xml` — UTF-8 encoded XML, one `<sms>` element per message
2. **Parsed dicts** → list of Python dicts with keys: `body`, `date`, `address`, `type`
3. **Normalized records** → same keys, values cleaned: ISO-8601 dates, E.164 phone numbers, `Decimal` amounts
4. **Categorized records** → adds `category` key: one of `incoming | outgoing | payment | airtime | unknown`
5. **SQLite rows** → upserted into `transactions` table; `hash` column enforces idempotency
6. **JSON aggregates** → `dashboard.json` with keys: `total_transactions`, `by_category`, `by_month`, `top_contacts`
7. **Rendered charts** → bar/line charts in browser fed from `dashboard.json` (default) or FastAPI endpoints (optional)

## Design Decisions

**SQLite vs Postgres/MySQL** — SQLite requires zero infrastructure: no server process, no credentials, no network configuration. For the week-1 dataset the file-based approach is sufficient, and the database file can be committed to a demo branch and opened by any team member without setup. Swapping the connection layer for Postgres or MySQL later requires changing only the connection string and driver import in `load_db.py`; the ETL logic above it is unaffected.

**JSON export vs always-through-API** — Pre-generating `dashboard.json` at pipeline run time means the frontend can be hosted on GitHub Pages, Netlify, or any static file server without a running Python process. The FastAPI layer can supplement this by serving filtered or paginated data when needed, but it is never required for the default view. This keeps the simplest deployment path as simple as possible.

**Dead-letter pattern instead of fail-fast** — Aborting the pipeline on the first bad record would discard all valid records that follow it in the file. Routing failures to `data/logs/dead_letter/` instead lets the pipeline complete and maximises data yield. Each dead-lettered file contains the original input and the error detail, making manual inspection and targeted replay straightforward.

**lxml preferred but ElementTree acceptable** — lxml is significantly faster on large files and handles malformed or non-standard XML more gracefully through its recovery parser. However, lxml is a C-extension dependency that requires a binary install; ElementTree ships with CPython and works for the dataset sizes expected in week 1. The parsing module checks for lxml at import time and falls back transparently, so the pipeline runs on a clean Python environment without additional installation steps.

**Static frontend over SPA framework** — The frontend's role is to display pre-aggregated charts and a transaction table — a data display use case that does not require component state management, routing, or a virtual DOM. Using vanilla HTML, CSS, and JavaScript avoids introducing npm, a bundler, and a build step into a repository where the primary artefact is the Python pipeline. Teammates can open `index.html` directly in a browser without any tooling.

**Idempotency via hashing the SMS body** — SHA-256 hashing the raw `body` string of each SMS and storing the result as a `UNIQUE` column in the `transactions` table means that inserting the same message twice is a no-op. This allows the pipeline to be re-run against the same export, against an extended export that overlaps with a previous one, or after a partial failure, without producing duplicate rows or requiring a manual truncate step first.

## Visual Diagram

The editable source diagram is located at `docs/architecture/architecture.drawio` and should be opened with [app.diagrams.net](https://app.diagrams.net); the rendered PNG export is at `docs/architecture/architecture.png` and must be regenerated from that tool whenever the diagram changes. A Mermaid version of the high-level architecture is also embedded in the project [README](../README.md#-high-level-architecture) for quick reference without leaving the repository browser.
