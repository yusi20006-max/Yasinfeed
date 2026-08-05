import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Callable, Any, Dict, List, Optional

@dataclass
class Job:
    name: str
    func: Callable[..., Any]
    interval: float  # in seconds
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    enabled: bool = True

    # Execution Tracking
    last_run_start: Optional[datetime] = None
    last_run_end: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_status: Optional[str] = "pending"  # pending, running, success, failed
    last_error: Optional[str] = None
    last_duration: Optional[float] = None  # in seconds

    def to_dict(self) -> dict:
        """Returns a dictionary representation of job status/metadata."""
        return {
            "name": self.name,
            "interval": self.interval,
            "enabled": self.enabled,
            "last_run_start": self.last_run_start.isoformat() if self.last_run_start else None,
            "last_run_end": self.last_run_end.isoformat() if self.last_run_end else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_status": self.last_status,
            "last_error": self.last_error,
            "last_duration": self.last_duration
        }


class Scheduler:
    """
    Lightweight, thread-safe, and pure-Python scheduler that manages
    and executes periodic tasks inside background threads.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.jobs: Dict[str, Job] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.logger = logger or logging.getLogger("yasinfeed.scheduler.engine")

    def add_job(self, name: str, func: Callable[..., Any], interval: float, run_immediately: bool = False, *args, **kwargs) -> Job:
        """
        Registers a new periodic job.
        """
        if interval <= 0:
            raise ValueError("Interval must be a positive number of seconds.")

        with self._lock:
            if name in self.jobs:
                raise ValueError(f"Job with name '{name}' already exists.")

            now = datetime.now(timezone.utc)
            if run_immediately:
                next_run = now
            else:
                next_run = now + timedelta(seconds=interval)

            job = Job(
                name=name,
                func=func,
                interval=interval,
                args=args,
                kwargs=kwargs,
                next_run=next_run
            )
            self.jobs[name] = job
            self.logger.info("Registered periodic job: %s [interval: %.1fs, next run: %s]", name, interval, next_run)
            return job

    def remove_job(self, name: str) -> None:
        """
        Removes a registered job.
        """
        with self._lock:
            if name in self.jobs:
                del self.jobs[name]
                self.logger.info("Removed job: %s", name)
            else:
                raise KeyError(f"Job '{name}' not found.")

    def pause_job(self, name: str) -> None:
        """
        Pauses a job, preventing it from executing until resumed.
        """
        with self._lock:
            if name in self.jobs:
                self.jobs[name].enabled = False
                self.logger.info("Paused job: %s", name)
            else:
                raise KeyError(f"Job '{name}' not found.")

    def resume_job(self, name: str) -> None:
        """
        Resumes a paused job and updates its next execution run time.
        """
        with self._lock:
            if name in self.jobs:
                job = self.jobs[name]
                job.enabled = True
                job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval)
                self.logger.info("Resumed job: %s [next run: %s]", name, job.next_run)
            else:
                raise KeyError(f"Job '{name}' not found.")

    def get_job(self, name: str) -> Optional[Job]:
        """
        Retrieves a job by name.
        """
        with self._lock:
            return self.jobs.get(name)

    def list_jobs(self) -> List[Job]:
        """
        Returns a list of all registered jobs.
        """
        with self._lock:
            return list(self.jobs.values())

    def start(self) -> None:
        """
        Starts the background scheduler loop.
        """
        with self._lock:
            if self._running:
                self.logger.warning("Scheduler is already running.")
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="YasinFeedSchedulerLoop")
            self._thread.start()
            self.logger.info("Background scheduler loop started.")

    def stop(self) -> None:
        """
        Stops the background scheduler loop gracefully.
        """
        with self._lock:
            if not self._running:
                return
            self._running = False
            self.logger.info("Stopping background scheduler loop...")

        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
            self.logger.info("Background scheduler loop stopped.")

    def _run_loop(self) -> None:
        """
        Continuous polling loop running in the background thread.
        Triggers ready jobs.
        """
        while True:
            with self._lock:
                if not self._running:
                    break

            now = datetime.now(timezone.utc)
            jobs_to_run = []

            with self._lock:
                for job in self.jobs.values():
                    if job.enabled and job.next_run and now >= job.next_run and job.last_status != "running":
                        jobs_to_run.append(job)
                        job.last_status = "running"
                        job.last_run_start = now

            for job in jobs_to_run:
                # Execute each job in a separate daemon thread to avoid blocking the scheduler loop
                worker = threading.Thread(
                    target=self._execute_job,
                    args=(job,),
                    daemon=True,
                    name=f"YasinFeedJobWorker-{job.name}"
                )
                worker.start()

            time.sleep(0.1)

    def _execute_job(self, job: Job) -> None:
        """
        Executes a single job's callable and logs execution tracking stats.
        """
        start_time = time.time()
        start_dt = datetime.now(timezone.utc)
        self.logger.debug("Executing job: %s", job.name)

        try:
            # Execute actual callable
            job.func(*job.args, **job.kwargs)

            duration = time.time() - start_time
            end_dt = datetime.now(timezone.utc)

            with self._lock:
                job.run_count += 1
                job.success_count += 1
                job.last_status = "success"
                job.last_run_end = end_dt
                job.last_duration = duration
                job.next_run = end_dt + timedelta(seconds=job.interval)
                job.last_error = None

            self.logger.debug("Job %s executed successfully in %.3fs.", job.name, duration)

        except Exception as e:
            duration = time.time() - start_time
            end_dt = datetime.now(timezone.utc)
            error_msg = f"{type(e).__name__}: {str(e)}"

            with self._lock:
                job.run_count += 1
                job.failure_count += 1
                job.last_status = "failed"
                job.last_run_end = end_dt
                job.last_duration = duration
                job.next_run = end_dt + timedelta(seconds=job.interval)
                job.last_error = error_msg

            self.logger.error("Job %s failed after %.3fs: %s", job.name, duration, error_msg, exc_info=True)
