import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any

from yasinfeed.engine import BaseModule
from .metrics import Metrics

class MonitoringModule(BaseModule):
    """
    Monitoring and System Health Check Module for YasinFeed.
    Gathers metrics, performs health checks, and reports system status.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing monitoring module...")
        self.metrics = Metrics()
        # Initialize default metrics
        self.metrics.set("startup_time", datetime.now(timezone.utc).isoformat())
        self.metrics.set("api_requests", 0)
        self.metrics.set("articles_processed", 0)
        self.metrics.set("articles_fetched", 0)
        self.metrics.set("fetch_cycles", 0)
        return True

    def start(self) -> bool:
        self.logger.info("Monitoring module started.")
        # Log system health on startup
        try:
            health = self.perform_health_check()
            self.logger.info("Initial System Health Check: %s", health["status"])
            for check, detail in health["checks"].items():
                self.logger.info("  - %s: %s (%s)", check, detail["status"], detail.get("message", "ok"))
        except Exception as e:
            self.logger.error("Failed to log initial system health check: %s", e)
        return True

    def stop(self) -> bool:
        self.logger.info("Monitoring module stopped.")
        return True

    def perform_health_check(self) -> Dict[str, Any]:
        """
        Runs comprehensive system health checks across all loaded modules.
        """
        checks = {}
        status = "healthy"

        # 1. Check Storage / DB Connectivity
        storage = self.engine.modules.get("storage")
        if storage:
            try:
                # Attempt to list feed sources or articles to verify DB connection
                storage.list_feed_sources()
                checks["storage"] = {"status": "healthy", "message": "Database connection verified"}
            except Exception as e:
                checks["storage"] = {"status": "unhealthy", "message": f"Database query failed: {str(e)}"}
                status = "unhealthy"
        else:
            checks["storage"] = {"status": "unhealthy", "message": "Storage module not registered"}
            status = "unhealthy"

        # 2. Check Scheduler Status
        scheduler_mod = self.engine.modules.get("scheduler")
        if scheduler_mod:
            if scheduler_mod.enabled:
                checks["scheduler"] = {"status": "healthy", "message": "Scheduler is enabled and running"}
            else:
                checks["scheduler"] = {"status": "degraded", "message": "Scheduler is disabled"}
                if status == "healthy":
                    status = "degraded"
        else:
            checks["scheduler"] = {"status": "unhealthy", "message": "Scheduler module not registered"}
            status = "unhealthy"

        # 3. Check API Module
        api_mod = self.engine.modules.get("api")
        if api_mod:
            if hasattr(api_mod, "server") and api_mod.server:
                checks["api"] = {"status": "healthy", "message": f"API server listening on {api_mod.host}:{api_mod.port}"}
            else:
                checks["api"] = {"status": "unhealthy", "message": "API server not running"}
                status = "unhealthy"
        else:
            checks["api"] = {"status": "unhealthy", "message": "API module not registered"}
            status = "unhealthy"

        # 4. Check Disk Space / Environment
        try:
            # Simple check for write permission in data dir or current directory
            test_file = "health_check_write_test.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            checks["environment"] = {"status": "healthy", "message": "Write permission verified"}
        except Exception as e:
            checks["environment"] = {"status": "unhealthy", "message": f"Write test failed: {str(e)}"}
            status = "unhealthy"

        return {
            "status": "ok" if status in ("healthy", "degraded") else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Reports full system status including metrics and system info.
        """
        health = self.perform_health_check()

        # Calculate uptime
        uptime_seconds = 0.0
        startup_str = self.metrics.get("startup_time")
        if startup_str:
            try:
                startup_time = datetime.fromisoformat(startup_str)
                uptime_seconds = (datetime.now(timezone.utc) - startup_time).total_seconds()
            except Exception:
                pass

        # Python & OS details
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "pid": os.getpid(),
            "uptime_seconds": uptime_seconds
        }

        return {
            "status": health["status"],
            "timestamp": health["timestamp"],
            "service": "YasinFeed API Layer",
            "system": system_info,
            "metrics": self.metrics.all(),
            "checks": health["checks"]
        }
