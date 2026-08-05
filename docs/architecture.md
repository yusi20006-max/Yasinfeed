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
- **YasinHub:** Service manager and system coordinator. Handles process supervision, inter-service API routing, and system monitoring.
- **Yasin-Agent:** AI workflow logic, prompt planning, and automated curation decisions.
- **YasinCLI:** Multi-purpose CLI for direct operator queries and system configuration.

---

## Module Directory Deep-Dive

### 1. `yasinfeed/api`
- **Class:** `ApiModule`
- **Purpose:** Serve curated feeds to frontend clients (PWA).
- **Responsibility:** Exposes RESTful JSON endpoints. Does not host complex dashboards, but provides the raw data endpoints.

### 2. `yasinfeed/fetch`
- **Class:** `FetchModule`
- **Purpose:** Stream / poll incoming content sources.
- **Responsibility:** Connects to remote RSS, feeds, or scrapers. Emits raw feed structures.

### 3. `yasinfeed/models`
- **Class:** `ModelsModule`
- **Purpose:** Common entity definition.
- **Responsibility:** Standardizes Python `dataclasses` (e.g. `Article`, `FeedSource`) utilized by other modules to enforce static type-checking.

### 4. `yasinfeed/publisher`
- **Class:** `PublisherModule`
- **Purpose:** Distribute compiled outputs to delivery pipelines.
- **Responsibility:** Distributes content to channels: Eitaa messengers, custom RSS feeds, or PWA-compatible storage endpoints.

### 5. `yasinfeed/rewrite`
- **Class:** `RewriteModule`
- **Purpose:** Content processing and optimization.
- **Responsibility:** Formats, sanitizes, and rewrites feed content. Connects with agent/adaptor interfaces for summaries.

### 6. `yasinfeed/scheduler`
- **Class:** `SchedulerModule`
- **Purpose:** Manage background timers.
- **Responsibility:** Triggers periodic runs of `FetchModule` and `PublisherModule` based on intervals.

### 7. `yasinfeed/storage`
- **Class:** `StorageModule`
- **Purpose:** Persistent storage adapter.
- **Responsibility:** Manages SQLite database schemas, reads/writes feed cache, and logs historic publishing events.

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
