import pytest
from pydantic import ValidationError
from getway.core.models import DownloadRequest, JobStatus, ProgressEvent
from getway.core.errors import GetWayError, ExtractionError
from getway.core.extractor import MediaExtractor

def test_download_request_model():
    """Vérifie que le modèle de requête valide bien les URLs."""
    # URL valide
    req = DownloadRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert str(req.url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Plus de slash final
    assert req.audio_only is False

    # URL invalide doit lever une erreur Pydantic
    with pytest.raises(ValidationError):
        DownloadRequest(url="ce-n-est-pas-une-url")

        
def test_progress_event_model():
    """Vérifie la structure d'un événement de progression."""
    event = ProgressEvent(status=JobStatus.DOWNLOADING, progress=45.5)
    assert event.status == JobStatus.DOWNLOADING
    assert event.progress == 45.5
    assert event.error is None

def test_extractor_invalid_url():
    """Vérifie que l'extracteur lève bien une erreur sur une URL corrompue."""
    with pytest.raises((ExtractionError, Exception)):
        MediaExtractor.extract("https://url-totalement-fausse-qui-nexiste-pas.com/video")