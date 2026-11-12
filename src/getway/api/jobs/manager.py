from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from getway.api.schemas import APIDownloadRequest
from getway.core.downloader import MediaDownloader
from getway.core.errors import GetWayError
from getway.core.models import DownloadRequest, JobStatus, ProgressEvent
from getway.core.config import settings


class BackgroundJobManager:
    """In-process job tracking for a single API service instance."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._download_slots = threading.BoundedSemaphore(
            max(1, settings.max_concurrent_downloads)
        )

    def create_job(self, request: APIDownloadRequest) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._prune_expired_jobs()
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "progress": 0.0,
                "file_path": None,
                "error": None,
                "created_at": datetime.now(UTC),
            }
        return job_id

    def _prune_expired_jobs(self) -> None:
        cutoff = datetime.now(UTC) - timedelta(hours=12)
        download_dir = settings.download_dir.resolve()
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job["created_at"] < cutoff
            and job["status"] in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
        ]
        for job_id in expired:
            file_path = self._jobs[job_id].get("file_path")
            if file_path:
                path = Path(file_path)
                try:
                    if path.resolve().parent == download_dir:
                        path.unlink(missing_ok=True)
                except OSError:
                    pass
            del self._jobs[job_id]

    def get_job_status(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def get_file_path(self, job_id: str) -> Path | None:
        job = self.get_job_status(job_id)
        if not job or job["status"] != JobStatus.COMPLETED or not job["file_path"]:
            return None
        path = Path(job["file_path"])
        return path if path.is_file() else None

    def _update_progress(self, job_id: str, event: ProgressEvent) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job["status"] = event.status
                job["progress"] = event.progress

    def run_download(self, job_id: str, request: APIDownloadRequest) -> None:
        with self._download_slots:
            with self._lock:
                if job_id not in self._jobs:
                    return
                self._jobs[job_id]["status"] = JobStatus.DOWNLOADING

            try:
                core_request = DownloadRequest(
                    url=request.url,
                    format_id=request.format_id,
                    audio_only=request.audio_only,
                    audio_format=request.audio_format,
                    output_dir=settings.download_dir,
                )
                downloader = MediaDownloader(output_dir=settings.download_dir)
                final_file = downloader.download(
                    core_request,
                    callback=lambda event: self._update_progress(job_id, event),
                )
                with self._lock:
                    job = self._jobs[job_id]
                    job.update(
                        status=JobStatus.COMPLETED,
                        file_path=str(final_file),
                        progress=100.0,
                    )
            except GetWayError as error:
                self._fail_job(job_id, error.message)
            except Exception as error:
                self._fail_job(job_id, str(error))

    def _fail_job(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.update(status=JobStatus.FAILED, error=message)


job_manager = BackgroundJobManager()
