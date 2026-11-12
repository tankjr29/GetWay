from pydantic import BaseModel, HttpUrl
from getway.core.models import JobStatus

class APIInfoRequest(BaseModel):
    url: HttpUrl

class APIDownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str | None = None
    audio_only: bool = False
    audio_format: str = "mp3"

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    progress: float = 0.0
    file_path: str | None = None
    error: str | None = None
