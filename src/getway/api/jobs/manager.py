import uuid
import asyncio
from pathlib import Path
from getway.core.downloader import MediaDownloader
from getway.core.models import DownloadRequest, JobStatus, ProgressEvent
from getway.core.errors import GetWayError

class BackgroundJobManager:
    def __init__(self):
        self._jobs: dict[str, dict] = {}
        # Pour gérer les abonnements SSE par job
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def create_job(self, request) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "status": JobStatus.PENDING,
            "progress": 0.0,
            "file_path": None,
            "error": None
        }
        self._subscribers[job_id] = []
        return job_id

    def get_job_status(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if job_id in self._subscribers:
            self._subscribers[job_id].append(queue)
        return queue

    async def _notify_subscribers(self, job_id: str, data: dict):
        if job_id in self._subscribers:
            for queue in self._subscribers[job_id]:
                await queue.put(data)

    def run_download(self, job_id: str, request):
        # Exécution synchrone du téléchargement encapsulée pour le thread d'arrière-plan
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self._jobs[job_id]["status"] = JobStatus.DOWNLOADING
        
        downloader = MediaDownloader()
        core_request = DownloadRequest(
            url=request.url,
            format_id=request.format_id,
            audio_only=request.audio_only,
            audio_format=request.audio_format
        )

        def api_progress_hook(event: ProgressEvent):
            if job_id in self._jobs:
                self._jobs[job_id]["progress"] = event.progress
                self._jobs[job_id]["status"] = event.status
                
                # Notification en temps réel
                payload = {
                    "status": event.status,
                    "progress": event.progress,
                    "speed": event.speed,
                    "eta": event.eta
                }
                asyncio.run_coroutine_threadsafe(self._notify_subscribers(job_id, payload), loop)

        try:
            final_file = downloader.download(core_request, callback=api_progress_hook)
            self._jobs[job_id]["status"] = JobStatus.COMPLETED
            self._jobs[job_id]["file_path"] = str(final_file)
            self._jobs[job_id]["progress"] = 100.0
            
            completed_payload = {"status": JobStatus.COMPLETED, "progress": 100.0, "file_path": str(final_file)}
            loop.run_until_complete(self._notify_subscribers(job_id, completed_payload))
            
        except GetWayError as e:
            self._jobs[job_id]["status"] = JobStatus.FAILED
            self._jobs[job_id]["error"] = e.message
            error_payload = {"status": JobStatus.FAILED, "error": e.message}
            loop.run_until_complete(self._notify_subscribers(job_id, error_payload))
        except Exception as e:
            self._jobs[job_id]["status"] = JobStatus.FAILED
            self._jobs[job_id]["error"] = str(e)
            error_payload = {"status": JobStatus.FAILED, "error": str(e)}
            loop.run_until_complete(self._notify_subscribers(job_id, error_payload))

job_manager = BackgroundJobManager()