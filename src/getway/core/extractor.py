import yt_dlp
from getway.core.errors import ExtractionError, InvalidURLError
from getway.core.models import MediaFormat, MediaInfo


class MediaExtractor:
    @staticmethod
    def extract(url: str) -> MediaInfo:
        """Extrait les métadonnées et les formats disponibles d'une URL."""
        ydl_opts = {
            'extract_flat': False,
            'skip_download': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ExtractionError("Impossible de récupérer les informations de la vidéo.")

                formats = []
                for f in info.get('formats', []):
                    # On filtre les formats basiques pour garder l'essentiel
                    formats.append(
                        MediaFormat(
                            format_id=f.get('format_id', ''),
                            ext=f.get('ext', ''),
                            resolution=f.get('resolution') or f.get('format_note'),
                            fps=f.get('fps'),
                            vcodec=f.get('vcodec'),
                            acodec=f.get('acodec'),
                            filesize=f.get('filesize') or f.get('filesize_approx'),
                            format_note=f.get('format_note'),
                        )
                    )

                return MediaInfo(
                    id=str(info.get('id', '')),
                    title=info.get('title', 'Titre inconnu'),
                    url=url,
                    duration=info.get('duration'),
                    uploader=info.get('uploader'),
                    thumbnail=info.get('thumbnail'),
                    formats=formats,
                )

        except Exception as e:
            if "Unsupported URL" in str(e):
                raise InvalidURLError(f"L'URL fournie n'est pas supportée : {url}")
            raise ExtractionError(f"Erreur lors de l'extraction des données", details=str(e))