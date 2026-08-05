# YasinFeed - Database Layer Architecture

This document describes the design, modular database abstraction, default SQLite implementation, and how to extend the database layer for other database providers in YasinFeed.

---

## Architecture Overview

The database layer under `yasinfeed/database/` implements a highly modular and extensible provider-based architecture, decoupling high-level storage requirements from the underlying persistent storage backends (such as SQLite, PostgreSQL, or MySQL).

```
 ┌───────────────────────────────────────────────┐
 │                 StorageModule                 │ (High-level Engine Module)
 └───────────────────────┬───────────────────────┘
                         │
                         ▼
 ┌───────────────────────────────────────────────┐
 │               create_db_provider()            │ (Provider Factory)
 └───────────────────────┬───────────────────────┘
                         │
                         ├─────────────────────────────────────────┐
                         ▼                                         ▼
         ┌───────────────────────────────┐         ┌───────────────────────────────┐
         │     SQLiteDatabaseProvider    │         │      PostgreSQLProvider       │ (Future extension)
         └───────────────────────────────┘         └───────────────────────────────┘
```

---

## Core Components

The database package consists of the following key files:

1. **`yasinfeed/database/base.py`**
   - Defines the `BaseDatabaseProvider` abstract base class.
   - Declares common exception classes (`DatabaseError`, `DatabaseConfigurationError`, `DatabaseConnectionError`).
   - Standardizes the CRUD operations on key entities: `FeedSource` and `Article`.

2. **`yasinfeed/database/sqlite.py`**
   - The default concrete database provider utilizing Python's built-in `sqlite3` library.
   - Guarantees 100% out-of-the-box compatibility with Linux and Termux on Android without requiring external binaries or libraries.
   - Standardizes on standard Row factory and atomic UPSERT queries (`ON CONFLICT(id) DO UPDATE SET`).

3. **`yasinfeed/database/factory.py`**
   - Implements `create_db_provider(provider_name, config)`.
   - Dynamically resolves the configured provider name and returns the instantiated class.

4. **`yasinfeed/database/models.py`**
   - Re-exports standard database-friendly models and entities for direct integration inside the package.

---

## Configuration

The database connection is managed via the `storage` configuration block (typically under `config/config.yaml`):

```yaml
storage:
  type: sqlite
  path: data/yasinfeed.db
```

---

## Extending the Database Layer with a New Provider

Adding support for other SQL database engines (such as PostgreSQL or MySQL) is straightforward and preserves full system compatibility:

1. **Create the Provider Class:**
   Create a new file under `yasinfeed/database/` (e.g. `postgresql.py`) subclassing `BaseDatabaseProvider` and implementing the abstract methods:
   ```python
   from typing import Optional, List, Dict, Any
   from yasinfeed.models import FeedSource, Article
   from yasinfeed.database.base import BaseDatabaseProvider

   class PostgreSQLDatabaseProvider(BaseDatabaseProvider):
       def validate_config(self) -> None:
           # Validate that host, port, dbname, user, password exist
           pass

       def connect(self) -> None:
           # Establish connection pool using psycopg2 or pg8000
           pass

       def save_feed_source(self, feed_source: FeedSource) -> None:
           # Perform upsert on postgresql
           pass

       # Implement other abstract CRUD methods...
   ```

2. **Register the Provider in the Factory:**
   Open `yasinfeed/database/factory.py` and register the new provider class:
   ```python
   from yasinfeed.database.postgresql import PostgreSQLDatabaseProvider

   PROVIDERS: Dict[str, Type[BaseDatabaseProvider]] = {
       "sqlite": SQLiteDatabaseProvider,
       "postgresql": PostgreSQLDatabaseProvider,
   }
   ```

3. **Configure the System:**
   Update your `config.yaml` to utilize the new database provider:
   ```yaml
   storage:
     type: postgresql
     host: localhost
     port: 5432
     dbname: yasinfeed
     user: postgres
     password: securepassword
   ```
