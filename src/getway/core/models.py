from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl


class JobStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MediaFormat(BaseModel):
    format_id: str
    ext: str
    resolution: str | None = None
    fps: float | None = None
    vcodec: str | None = None
    acodec: str | None = None
    filesize: int | None = None  # en octets
    format_note: str | None = None


class MediaInfo(BaseModel):
    id: str
    title: str
    url: str
    duration: int | None = None  # en secondes
    uploader: str | None = None
    thumbnail: str | None = None
    formats: list[MediaFormat] = Field(default_factory=list)


class DownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str | None = None
    audio_only: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    output_dir: Path | None = None


class ProgressEvent(BaseModel):
    status: JobStatus
    progress: float = Field(ge=0.0, le=100.0, default=0.0)
    speed: float | None = None      # octets/sec
    eta: int | None = None          # secondes restantes
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    filename: str | None = None
    error: str | None = None