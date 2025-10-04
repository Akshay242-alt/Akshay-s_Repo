from __future__ import annotations

from datetime import datetime
from threading import Thread, Event
from time import sleep

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


class SimpleScheduler:
    def __init__(self, interval_seconds: int = 3600):
        self.interval_seconds = interval_seconds
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                pass
            self._stop.wait(self.interval_seconds)

    def _tick(self):
        # Placeholder for periodic tasks like fetching external data or retraining
        with SessionLocal() as db:
            self._do_housekeeping(db)

    def _do_housekeeping(self, db: Session):
        # Intentionally minimal; extend as needed
        _ = db
        return
