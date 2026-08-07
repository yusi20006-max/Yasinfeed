# YasinFeed - System Architecture

This document describes the architectural layout, modules, and lifecycle management of YasinFeed.

---

## Architectural Principles

YasinFeed has been designed with four core engineering goals in mind:
1. **Separation of Concerns:** Keep core data pipelines separate from command-line tools, AI agent decision logic, and service supervisors.
2. **Modular Composition:** Modules are decoupled and communicate via standardized interface schemas (e.g. `BaseModule`). They can be replaced or extended independently.
3. **Environment Compatibility:** Ensure out-of-the-box compatibility with standard Linux distributions and Termux Android setups by keeping dependencies minimal and pure Python.
4. **Lifecycle Safety:** Handle service states (Initialization, Startup, Shutdown) gracefully to prevent resource leaks, database corruption, or socket lockups.

---

## High-Level Layout

The system is split into three main architectural planes:

```
                  ┌───────────────────────────────┐
                  │          YasinHub / CLI       │ (External Control Plane)
                  └───────────────┬───────────────┘
                                  │ (REST/Hooks)
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                           YasinFeed                              │ (Core Data Plane)
│                                                                  │
│  ┌───────────────────────┐             ┌──────────────────────┐  │
│  │      ApiModule        ├────────────►│   SchedulerModule    │  │
│  └───────────────────────┘             └──────────┬───────────┘  │
│                                                   │              │
│  ┌───────────────────────┐             ┌──────────▼───────────┐  │
│  │      FetchModule      ├────────────►│    RewriteModule     │  │
│  └───────────────────────┘             └──────────┬───────────┘  │
│                                                   │              │
│  ┌───────────────────────┐             ┌──────────▼───────────┐  │
│  │     StorageModule     │◄────────────┤   PublisherModule    │  │
│  └───────────────────────┘             └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Separation of Concerns: Ecosystem Overview

The wider YasinFeed ecosystem is separated across the following boundaries to prevent monolith sprawl:

- **YasinFeed (This Component):** The central engine that fetches raw streams, rewrites articles, and prepares final RSS, PWA, or Eitaa outputs.
- **YasinHub (Do NOT implement here):** Service manager and system coordinator. Handles process supervision, inter-service API routing, and system monitoring.
- **Yasin-Agent (Do NOT implement here):** AI workflow logic, prompt planning, and automated curation decisions.
- **YasinCLI (Do NOT implement here):** Multi-purpose CLI for direct operator queries and system configuration.

---

## Module Directory Deep-Dive & Extension Points

Each of the seven core modules has been designed for extreme modularity and clean boundaries.

### 1. `yasinfeed/api`
- **Class:** `ApiModule`
- **Purpose:** Serve curated feeds to frontend clients (PWA) and external integrations.
- **Responsibility:** Exposes RESTful JSON endpoints. Does not host complex dashboards, but provides raw data and health endpoints.
- **Future Extension Points:**
  - Standardized JSON REST/GraphQL controllers for third-party consumers.
  - Adding lightweight WebSockets support or Server-Sent Events (SSE) for real-time article delivery on Termux/Linux.

### 2. `yasinfeed/fetch`
- **Class:** `FetchModule`
- **Purpose:** Stream / poll incoming content sources.
- **Responsibility:** Connects to remote RSS, Atom feeds, custom JSON feeds, or scrapers. Emits raw feed structures standardized as internal models.
- **Future Extension Points:**
  - Creating custom fetcher adapters (e.g., standard RSS parser, HTML scraper, Telegram channel listener, Twitter/X scraper).
  - High-performance asynchronous feed polling loops utilizing `asyncio`.

### 3. `yasinfeed/models`
- **Class:** `ModelsModule`
- **Purpose:** Common entity definition.
- **Responsibility:** Standardizes Python `dataclasses` (e.g. `Article`, `FeedSource`) utilized by other modules to enforce static type-checking and clear schema definitions.
- **Future Extension Points:**
  - Extensible fields for AI metadata tagging, language classification, or category assignment.
  - Serialization adapters (to/from JSON, XML, or database rows).

### 4. `yasinfeed/publisher`
- **Class:** `PublisherModule`
- **Purpose:** Distribute compiled outputs to delivery pipelines.
- **Responsibility:** Distributes structured, curated content to output channels: Eitaa messengers, custom RSS feeds, or PWA-compatible storage endpoints.
- **Future Extension Points:**
  - Adapting outputs for new publishing channels (e.g. Telegram, Discord Webhooks, Bluesky, Mastodon).
  - Customizable formatting templates for Eitaa message bodies.

### 5. `yasinfeed/rewrite`
- **Class:** `RewriteModule`
- **Purpose:** Content processing, summarization, translation, and optimization.
- **Responsibility:** Formats, sanitizes, and rewrites feed content. Connects with modular AI provider architecture (`BaseAIProvider`) to rewrite feed text.
- **Architecture Details:** See `docs/ai_providers.md` for full implementation and interface specs.
- **Supported Providers:**
  - `dummy`: Offline testing/dry-run provider.
  - `openai`: OpenAI-compatible endpoint provider (using standard `urllib.request`). Perfect for official OpenAI models or local proxy servers (Ollama, LM Studio).
  - `huggingface`: Hugging Face Serverless Inference provider (using standard `urllib.request`).
- **Future Extension Points:**
  - Adding offline translate providers or other custom local-first modules.
  - Modular preprocessing pipelines (regex sanitizer, profanity filter, HTML cleaner).

### 6. `yasinfeed/scheduler`
- **Class:** `SchedulerModule`
- **Purpose:** Manage background timers.
- **Responsibility:** Triggers periodic runs of `FetchModule` and `PublisherModule` based on configurable intervals.
- **Future Extension Points:**
  - Support for cron-like schedules.
  - Dynamic scheduling (e.g., adapt scheduling interval based on feed update frequency).

### 7. `yasinfeed/storage`
- **Class:** `StorageModule`
- **Purpose:** Persistent storage adapter.
- **Responsibility:** Manages database connections, schemas, reads/writes feed cache, and logs historic publishing events.
- **Future Extension Points:**
  - Pluggable backends: Built-in `SQLiteStorage` for lightweight SQLite persistence and `JSONStorage` for flat-file JSON serialization.
  - Automatic migrations runner when the schema upgrades.

---

## Application Lifecycle Flow

YasinFeed strictly coordinates startup and shutdown sequences to keep the runtime clean and trace-free.

### 1. Initialization (`initialize()`)
1. **Config Loading:** The engine loads values from `config/config.yaml`, merges them with safe code defaults, and applies `YASINFEED_` environment variable overrides.
2. **Logging Foundation:** Sets up the root logger handlers for stdout/console and writes logs to file (e.g., `yasinfeed.log`).
3. **Module Instantiation:** Imports and registers the 7 modules.
4. **Ordered Initialize:** Runs `.initialize()` on each module in dependency-friendly order:
   `storage` ➔ `models` ➔ `rewrite` ➔ `fetch` ➔ `publisher` ➔ `scheduler` ➔ `api`

### 2. Execution (`start()`)
1. Runs `.start()` on all registered modules in initialization order.
2. Starts periodic fetch loops and binds API server ports.
3. Main thread enters an interruptible wait sleep loop.

### 3. Graceful Shutdown (`stop()`)
Upon receiving `SIGINT` (Ctrl+C) or `SIGTERM`:
1. The engine catches the signal and calls `stop()`.
2. Loops through modules in **reverse order** (`api` first, `storage` last) calling `.stop()`.
3. Modules close active connections, cancel timers, and release bound ports cleanly.
4. Main thread finishes sleep loop and exits.

---

## Multi-Source Aggregation Flow

YasinFeed aggregates content fetched from multiple sources, manages priorities/weights, and detects duplicates:

1. **Failure-Isolated Fetch Loop**: The `FetchModule` queries all enabled `FeedSource` entities from database. Each fetch runs independently. If one feed fails (e.g., timeout), the failure is isolated and other sources are fetched normally.
2. **Reliability Tracking**: With every fetch cycle, source statistics (`fetch_count`, `success_count`, `failure_count`, `last_error`) are updated, and the source `reliability_score` is dynamically calculated and saved back to storage.
3. **Improved Retries**: Feed fetches employ exponential backoff with configurable retries to handle intermittent network failures.
4. **Duplicate Detection across Sources**: Fetched articles are grouped together by identical URL/ID or normalized title similarity.
5. **Content Merge Strategy**: For duplicates, a merge strategy determines the final content:
   - `priority`: Sorts duplicate candidates by source priority, weight, and reliability score, keeping the article from the highest-ranked source.
   - `combine`: Merges unique content sections across all sources into a single unified article.

---

## Security Architecture

The API and Authentication modules implement layered security middleware:

1. **IP-Based Rate Limiting**: REST request handlers enforce strict, rolling-window request rate limits to prevent denial-of-service and brute-force attacks.
2. **Security Headers**: Standard headers are injected into all HTTP responses (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Content-Security-Policy`, and `Strict-Transport-Security`).
3. **API Key & Token Authentication**: Support for both session tokens (Bearer tokens) and system-wide API keys (`X-API-Key` or `Authorization: Key <api_key>`).
4. **Role-Based Permission Enforcement**: Protects sensitive endpoints by matching user roles (`admin` or `viewer`) against required route permissions before serving resources.

---

## Observability Architecture (Issue #44)

YasinFeed contains a high-performance, thread-safe, and pure-Python observability engine embedded under `yasinfeed/monitoring/`.

### 1. Central Metrics Engine
- **Class:** `Metrics`
- **Scope:** Thread-safe state tracker using a `threading.Lock` wrapper.
- **KPIs Tracked:**
  - `fetch_cycles`: Cumulative fetch pipelines executed.
  - `articles_fetched`: Cumulative raw entries gathered.
  - `articles_processed`: Cumulative items transformed successfully.
  - `total_errors` and `errors_<component>_total`: Counter for recorded failures.
- **Performance Profiling:** Supports a `.timing(name)` context manager and `.time_func(name)` decorator tracking active performance runtimes (last duration, peak runtimes, execution counts, and running averages).

### 2. Structured JSON Event Logging
- **Class:** `StructuredEventLogger`
- **Target File:** `config/events.json` (JSON Lines format)
- **Formatting:** Captures events containing standardized fields: `timestamp`, `event_type`, `severity`, `module`, `message`, and structured `details` metadata. This supports seamless diagnostic tracing and log ingestion for downstream indexers.

---

## Integration Architecture (Issue #45)

YasinFeed provides a unified, provider-agnostic, and decoupled communication plane under `yasinfeed/integration/` to coordinate with other Yasin Ecosystem products without direct dependency compile locks.

```
                          ┌────────────────────────┐
                          │   IntegrationModule    │
                          └───────────┬────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
   ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
   │    Local Hooks   │      │   Yasin-Hub      │      │   Yasin-Agent    │
   │    (Callables)   │      │   (Provider)     │      │   (Provider)     │
   └──────────────────┘      └──────────────────┘      └──────────────────┘
```

### 1. Integration Abstraction & Provider Interfaces
- **`BaseIntegrationProvider`**: Standard abstract base class defining lifecycle hook (`on_register`) and communication endpoint (`on_event`).
- **`HubIntegrationProvider`**: Concrete interface template with specialized methods to export dynamic REST routes (`register_routes`) and heartbeat diagnostic indicators (`notify_hub_status`).
- **`AgentIntegrationProvider`**: Concrete interface template specialized in asynchronous planning dispatches (`dispatch_agent_task`) and post-rewrite rating collections (`retrieve_agent_review`).

### 2. Event Hooks System
An event dispatching manager supports reactive event propagation:
- **Registered Hooks:** Supports subscribing dynamic callbacks on specific event types (e.g., `on_startup`, `on_shutdown`, `on_pipeline_start`, `on_pipeline_complete`, `on_article_fetched`, and `on_error`).
- **Trigger Dispatch:** Calling `trigger_event` notifies registered callbacks and forwards the payload safely to active integration providers.

### 3. Extension Points & Plugin-Ready Architecture
- **Class:** `PluginLoader`
- **Purpose:** Compiles and loads dynamic provider plugins from configured folders or files on the file system.
- **Capability:** Uses pure Python `importlib` and reflection techniques to locate and register class attributes subclassing `BaseIntegrationProvider` and calls dynamic module setup hooks (`register_plugin`) dynamically without altering central YasinFeed code.
