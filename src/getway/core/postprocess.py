from pathlib import Path
import subprocess
from getway.core.errors import FFmpegError


class FFmpegProcessor:
    @staticmethod
    def verify_ffmpeg() -> bool:
        """Vérifie si FFmpeg est accessible dans le PATH système."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def convert_audio(input_file: Path, output_file: Path, codec: str = "mp3", quality: str = "192k") -> Path:
        """Convertit un fichier média en audio via FFmpeg."""
        if not input_file.exists():
            raise FFmpegError(f"Le fichier d'entrée n'existe pas : {input_file}")

        cmd = [
            "ffmpeg", "-y", "-i", str(input_file),
            "-vn", "-ab", quality, "-acodec", codec, str(output_file)
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_file
        except subprocess.CalledProcessError as e:
            raise FFmpegError("Échec de la conversion FFmpeg", details=e.stderr.decode())