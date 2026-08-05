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
