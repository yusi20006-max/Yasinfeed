# YasinFeed - Core Foundation

YasinFeed is the production-ready core engine responsible for gathering raw content streams, processing/summarizing articles, and preparing outputs for multiple channels.

## Project Purpose

YasinFeed operates as a lightweight, clean, and highly modular backend service. It specializes in:
1. **Collecting Content Sources:** Fetching feeds, blogs, or custom raw streams.
2. **Processing & Rewriting Content:** Structuring raw feeds and sanitizing/rewriting them to target output standards (e.g. AI-driven summary/translation).
3. **Preparing Content Outputs:** Formatting data structures to prepare publishing pipelines.
4. **Publishing Content Outputs:** Offering RSS feeds, PWA-compatible JSON endpoints, and Eitaa publishing channels.

### Separation of Responsibilities & Ecosystem Boundaries

To ensure a clean architecture, responsibilities are clearly separated across distinct components:
- **YasinFeed (This repository):** Only handles content collection, processing, and publishing stubs/pipes. It remains lightweight and modular.
- **YasinHub (Do NOT implement here):** Service management and system coordination (orchestration).
- **Yasin-Agent (Do NOT implement here):** Agent workflows, decision making, and automation.
- **YasinCLI (Do NOT implement here):** Command-line user interface.

YasinFeed **does not** function as an orchestrator, command CLI manager, or agent execution framework.

---

## Architecture and Modules

YasinFeed's system architecture maintains a strict, decoupled layout:

```
yasinfeed/
├── api/          # Exposes endpoints for PWAs and integration
├── fetch/        # Collecting raw feeds and monitoring sources
├── models/       # Core data models, schemas, and typings
├── publisher/    # Disseminating outputs (Eitaa, PWA data, RSS output)
├── rewrite/      # Content rewriting, summarization, and translation
├── scheduler/    # Periodic task execution & background polling
├── storage/      # Persistence layer (e.g. SQLite database, JSON files)
├── config.py     # Hierarchical configuration loading (YAML + Env Var)
├── logging.py    # Log handlers (Console & File log configurations)
└── engine.py     # Central application lifecycle manager (Initialize/Start/Stop)
```

### Module Responsibilities & Extension Points

1. **`api`**: Serves as the query/delivery layer. Exposes structured PWA-compatible data sources and health endpoints.
   - *Extension Points:* WebSockets for live updates, standardized REST/GraphQL endpoints.
2. **`fetch`**: Handles connections to remote streams, parsing RSS feeds, and standardizing inbound content items.
   - *Extension Points:* Scraper modules, social media stream adapters (Telegram, Twitter/X, Mastodon).
3. **`rewrite`**: Coordinates raw content transformation. Interfaces with agent/pipeline adapters to rewrite/summarize feed text.
   - *Extension Points:* LLM adapters (Ollama, OpenAI, Claude), multi-lingual translation APIs.
4. **`storage`**: Deals with database/file read/write operations, supporting SQLite persistence.
   - *Extension Points:* Pluggable backends (`SQLiteStorage`, `JSONStorage`), automated database migrations.
5. **`scheduler`**: A cyclic task execution layer triggering automated fetching/rewriting/publishing loops.
   - *Capabilities:* Thread-safe background execution, job management (pause, resume, add, and remove jobs), and comprehensive execution tracking (start/end times, execution duration, run counts, failure error messages).
   - *Default Automation Pipeline:* Registers a default pipeline job `fetch_and_process` running at configured fetch intervals. This automatically orchestrates the entire cycle: fetching raw content streams from `fetch` module, creating/saving articles to `storage`, rewriting them with standard/AI summary layers via `rewrite`, and publishing/distributing to Eitaa, RSS, or PWA endpoints via `publisher`.
   - *Extension Points:* Advanced cron schedules, back-off retry timings.
6. **`publisher`**: Adapts content to feed endpoints: Eitaa messaging, PWA client endpoints, and XML-compliant RSS.
   - *Extension Points:* New delivery channels (Bluesky, Discord), customizable rich formatting.
7. **`models`**: Standardizes shared entities like `Article` and `FeedSource` across all modules.
   - *Extension Points:* Multi-layer classification metadata, tags.

---

## Configuration

YasinFeed supports multi-tiered configuration loading.

### Configuration Hierarchy
1. **Defaults:** Safe fallback options defined in code.
2. **YAML Config:** Parsed from `config/config.yaml` or defined via `YASINFEED_CONFIG_PATH`.
3. **Environment Variables:** Highest priority overrides starting with `YASINFEED_`.

### Environment Overrides
- **Direct variables:**
  - `YASINFEED_ENV` (maps to `app.env`)
  - `YASINFEED_PORT` (maps to `api.port`)
  - `YASINFEED_HOST` (maps to `api.host`)
  - `YASINFEED_LOG_LEVEL` (maps to `logging.level`)
- **Nested variables:** Use double underscores (`__`) to target any arbitrary nested config key. For example:
  - `YASINFEED__PUBLISHER__EITAA__ENABLED=true`
  - `YASINFEED__FETCH__INTERVAL_SECONDS=60`

---

## Installation & Running

### Requirements
- Python `>= 3.8`
- Minimal dependencies (compatible with Termux and Linux environments)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Run YasinFeed
```bash
python -m yasinfeed.main
```

---

## Development Workflow

### Adding Features / Modifying Code
1. Code developed on feature branch: `feature/issue-1-core-foundation`
2. Follow standard coding guidelines (PEP 8, modular coupling, clean abstraction).
3. Do not directly integrate heavy AI models or agent frameworks inside the core. Use interfaces or adapter stubs.

### Running Tests
The project uses the standard Python `unittest` framework to execute tests without adding heavy external testing libraries.

Run the test suite:
```bash
python -m unittest discover -v
```

---

## Production Release & Deployment

For production rollouts and maintenance, refer to our comprehensive deployment assets:

- 📥 **[Installation Guide](docs/installation.md):** Step-by-step setup instructions for Linux and Termux.
- 🚀 **[Deployment Guide](docs/deployment.md):** Process management (CLI, systemd, Termux-services), directory layout, and security specs.
- 📋 **[Production Checklist](docs/production_checklist.md):** Pre-release auditing checklist for production-ready setups.
- 📄 **[Release Notes Template](docs/release_notes_template.md):** Standard template for formatting and tracking release notes.
