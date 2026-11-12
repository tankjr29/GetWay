class GetWayError(Exception):
    """Exception de base pour toutes les erreurs liées à GetWay."""

    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ExtractionError(GetWayError):
    """Échec lors de l'analyse de l'URL ou de la récupération des métadonnées."""


class DownloadError(GetWayError):
    """Échec lors du téléchargement des flux vidéo/audio."""


class FFmpegError(GetWayError):
    """Échec lors de la fusion ou de la conversion avec FFmpeg."""


class InvalidURLError(GetWayError):
    """L'URL fournie est invalide ou non supportée."""