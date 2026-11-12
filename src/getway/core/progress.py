from typing import Protocol
from getway.core.models import ProgressEvent

class ProgressCallback(Protocol):
    """Protocole que tout écouteur de progression (CLI, API, Log) doit implémenter."""
    
    def __call__(self, event: ProgressEvent) -> None:
        ...