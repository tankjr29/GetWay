from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from getway.core.config import settings
from getway.core.downloader import MediaDownloader
from getway.core.errors import GetWayError
from getway.core.extractor import MediaExtractor
from getway.core.models import DownloadRequest, JobStatus, ProgressEvent
from getway.core.postprocess import FFmpegProcessor

app = typer.Typer(
    name="getway",
    help="GetWay - Moteur de téléchargement média rapide et modulaire.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def info(url: str = typer.Argument(..., help="URL de la vidéo à analyser")):
    """Affiche les informations et les formats disponibles d'une vidéo."""
    with console.status("[bold cyan]Extraction des métadonnées...[/bold cyan]", spinner="dots"):
        try:
            media = MediaExtractor.extract(url)
        except GetWayError as e:
            console.print(f"[bold red]❌ {e.message}[/bold red]")
            if e.details:
                console.print(f"[dim]{e.details}[/dim]")
            raise typer.Exit(code=1)

    # Affichage de la fiche récapitulative
    duration_str = f"{media.duration // 60}m {media.duration % 60}s" if media.duration else "Inconnue"
    console.print(
        Panel(
            f"[bold white]{media.title}[/bold white]\n"
            f"[cyan]Auteur :[/cyan] {media.uploader or 'Inconnu'}  |  "
            f"[cyan]Durée :[/cyan] {duration_str}",
            title="[bold green]Média détecté[/bold green]",
            border_style="green",
        )
    )

    # Tableau des formats
    table = Table(title="Formats disponibles", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Ext", style="green")
    table.add_column("Résolution / Note")
    table.add_column("Vidéo", style="dim")
    table.add_column("Audio", style="dim")
    table.add_column("Taille approx.", justify="right")

    for f in media.formats:
        size_mb = f"{f.filesize / (1024 * 1024):.1f} MB" if f.filesize else "-"
        table.add_row(
            f.format_id,
            f.ext,
            f.resolution or "-",
            f.vcodec or "-",
            f.acodec or "-",
            size_mb,
        )

    console.print(table)


@app.command()
def download(
    url: str = typer.Argument(..., help="URL de la vidéo à télécharger"),
    format_id: str | None = typer.Option(None, "--format", "-f", help="ID du format spécifique (voir commande info)"),
    audio: bool = typer.Option(False, "--audio", "-a", help="Extraire uniquement l'audio"),
    audio_format: str = typer.Option("mp3", "--audio-format", help="Format audio (mp3, m4a, wav...)"),
    output: Path = typer.Option(settings.download_dir, "--output", "-o", help="Dossier de destination"),
):
    """Télécharge une vidéo ou extrait sa piste audio."""
    if not FFmpegProcessor.verify_ffmpeg():
        console.print("[bold yellow]⚠️ Attention : FFmpeg n'est pas détecté dans le PATH. La fusion HD ou l'extraction audio risque d'échouer.[/bold yellow]")

    request = DownloadRequest(
        url=url,
        format_id=format_id,
        audio_only=audio,
        audio_format=audio_format,
        output_dir=output,
    )

    downloader = MediaDownloader(output_dir=output)

    # Configuration de la barre de progression Rich
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Initialisation...", total=100.0)

        # Implémentation concrète de notre protocole ProgressCallback
        def cli_progress_hook(event: ProgressEvent) -> None:
            if event.status == JobStatus.DOWNLOADING:
                desc = f"Téléchargement ({event.filename[:25]}...)" if event.filename else "Téléchargement..."
                total = float(event.total_bytes) if event.total_bytes else 100.0
                completed = float(event.downloaded_bytes) if event.downloaded_bytes else event.progress
                progress.update(task_id, description=desc, total=total, completed=completed)
            elif event.status == JobStatus.PROCESSING:
                progress.update(task_id, description="[yellow]Post-traitement FFmpeg...", completed=100.0, total=100.0)

        try:
            final_file = downloader.download(request, callback=cli_progress_hook)
            console.print(f"\n[bold green]✅ Terminé ! Fichier sauvegardé :[/bold green] {final_file}")
        except GetWayError as e:
            console.print(f"\n[bold red]❌ {e.message}[/bold red]")
            if e.details:
                console.print(f"[dim]{e.details}[/dim]")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()