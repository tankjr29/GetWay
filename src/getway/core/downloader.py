import os
from pathlib import Path
import yt_dlp
from getway.core.errors import DownloadError
from getway.core.models import DownloadRequest, JobStatus, ProgressEvent
from getway.core.progress import ProgressCallback


class MediaDownloader:
    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("./downloads")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, request: DownloadRequest, callback: ProgressCallback | None = None) -> Path:
        """Télécharge une vidéo ou extrait l'audio selon la requête."""
        output_path = request.output_dir or self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'noplaylist': True,
        }

        if request.audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': request.audio_format,
                    'preferredquality': request.audio_quality,
                }],
            })
        else:
            if request.format_id:
                ydl_opts['format'] = request.format_id
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'

        def ydl_progress_hook(d):
            if not callback:
                return

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100) if total > 0 else 0.0
                
                event = ProgressEvent(
                    status=JobStatus.DOWNLOADING,
                    progress=round(percent, 2),
                    speed=d.get('speed'),
                    eta=d.get('eta'),
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    filename=os.path.basename(d.get('filename', ''))
                )
                callback(event)

            elif d['status'] == 'finished':
                event = ProgressEvent(
                    status=JobStatus.PROCESSING,
                    progress=100.0,
                    filename=os.path.basename(d.get('filename', ''))
                )
                callback(event)

        ydl_opts['progress_hooks'] = [ydl_progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(str(request.url), download=True)
                filename = ydl.prepare_filename(info)
                
                if request.audio_only:
                    filename = str(Path(filename).with_suffix(f'.{request.audio_format}'))
                    
                return Path(filename)

        except Exception as e:
            if callback:
                callback(ProgressEvent(status=JobStatus.FAILED, error=str(e)))
            raise DownloadError(f"Erreur lors du téléchargement", details=str(e))