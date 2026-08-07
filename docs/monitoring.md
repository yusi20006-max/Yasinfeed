# YasinFeed Monitoring & Health Check System

This document describes the design, integration, endpoints, and metrics collection for the Monitoring and Health Check module implemented in YasinFeed.

---

## Architectural Principles

The Monitoring module (`yasinfeed/monitoring`) is designed to serve as a high-performance, lightweight system observability engine. It monitors the health of all registered core components, aggregates performance metrics, and logs state transitions cleanly.

### Termux & Linux Compatibility
To remain perfectly compatible with Linux and Termux on Android without third-party dependencies, the monitoring module utilizes pure-Python standard libraries. It calculates uptimes, gathers platform info, tracks PID details, and provides deep observability metrics without requiring any external system libraries or processes.

---

## Engine & Module Integration

The Monitoring module is integrated as a core module in YasinFeed.

1. **Lifecycle Management**: When the YasinFeed engine initializes, `MonitoringModule` is loaded early in the registration order. This ensures the metrics store is active and available before other modules start up.
2. **Metrics Store**: An in-memory, thread-safe metrics registry (`Metrics`) allows safe read and write updates across all concurrent background threads.
3. **Health Observability**: The module polls and probes the storage database connectivity, the scheduler thread status, write permissions to the file system, and API service binding to create a comprehensive multi-layered health status report.

---

## Metrics Registry Foundation

The system records real-time KPIs that can be consumed for performance dashboards and telemetry collectors:

- `startup_time`: ISO 8601 UTC timestamp indicating when the engine initialized.
- `api_requests`: Cumulative count of incoming REST API requests processed by the server.
- `articles_processed`: Number of articles successfully transformed and saved via processing pipelines.
- `articles_fetched`: Cumulative count of raw feed entries fetched from feed sources.
- `fetch_cycles`: Cumulative count of scheduled fetching pipeline executions.

---

## REST Endpoints Integration

When `MonitoringModule` is active, the unified `/health` REST endpoint automatically elevates to report full-system telemetry.

### 1. Integrated System Status
Returns comprehensive platform information, detailed component health states, and live metrics.

- **Path**: `/health` or `/api/health`
- **Method**: `GET`
- **Response**: `200 OK`
- **Payload Example**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-08-07T12:00:00.000000+00:00",
    "system": {
      "python_version": "3.12.1",
      "platform": "linux",
      "pid": 12345,
      "uptime_seconds": 124.5
    },
    "metrics": {
      "startup_time": "2026-08-07T11:58:00.000000+00:00",
      "api_requests": 42,
      "articles_processed": 12,
      "articles_fetched": 50,
      "fetch_cycles": 3
    },
    "checks": {
      "storage": {
        "status": "healthy",
        "message": "Database connection verified"
      },
      "scheduler": {
        "status": "healthy",
        "message": "Scheduler is enabled and running"
      },
      "api": {
        "status": "healthy",
        "message": "API server listening on 127.0.0.1:8000"
      },
      "environment": {
        "status": "healthy",
        "message": "Write permission verified"
      }
    }
  }
  ```

---

## Health Check Classifications

Component checks are categorized into three operational states:

1. **`healthy`**: The component is fully functional and ready for work (e.g., SQLite connection is valid, disk write tests succeed).
2. **`degraded`**: The component is loaded but running in an inactive or limited state (e.g., scheduler is disabled in config).
3. **`unhealthy`**: The component has failed or is inaccessible (e.g., database connection error, missing read/write permission).

---

## Detailed Telemetry & Performance Tracking

With the advanced Observability Layer (Issue #44) activated, the `/health` payload is dynamically populated with real-time performance timers and errors snapshots.

### 1. Performance Statistics
Performance tracking captures last duration, peak runtimes, execution counts, and running averages under the `metrics` section:
- `<operation>_last_duration_seconds`: Precision timing of the last block execution.
- `<operation>_executions_total`: Sum total of successful block operations.
- `<operation>_duration_seconds_total`: Cumulative duration sum.
- `<operation>_average_duration_seconds`: Running mean latency.

Supported operation blocks include:
- `fetch_sources`
- `fetch_and_process_pipeline`
- `db_save_article`, `db_get_article`, `db_list_articles`
- `db_save_feed_source`, `db_get_feed_source`, `db_list_feed_sources`
- `pipeline_stage_SanitizationStage`, `pipeline_stage_RewriteStage`, `pipeline_stage_TranslationStage`, `pipeline_stage_ContentAnalysisStage`, `pipeline_stage_MetadataTaggingStage`

### 2. Error Metrics
Detailed errors mapping records occurrences, type, description, and timestamp of the last recorded error per subsystem under the `errors` section:
```json
{
  "errors": {
    "total_errors": 1,
    "last_errors": {
      "fetch": {
        "type": "SourceFetchError",
        "message": "Source Name: Connection timeout",
        "timestamp": "2026-08-07T12:05:00Z"
      }
    }
  }
}
```

### 3. Structured Event Log (JSON Lines)
High-integrity events are written to `config/events.json` with standard structures:
```json
{"timestamp": "2026-08-07T12:00:00Z", "event_type": "article_processed", "severity": "INFO", "module": "rewrite", "message": "Article art-1 processed successfully through pipeline", "details": {"title": "Sample Title", "duration": 0.089}}
```
