from fastapi import FastAPI, BackgroundTasks, HTTPException
from getway.core.extractor import MediaExtractor
from getway.core.errors import GetWayError
from getway.api.schemas import APIInfoRequest, APIDownloadRequest, JobResponse
from getway.api.jobs import job_manager
from getway.core.models import JobStatus

app = FastAPI(
    title="GetWay API",
    description="API asynchrone pour le moteur de téléchargement GetWay",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API GetWay !", "status": "online"}

@app.post("/info")
def get_media_info(payload: APIInfoRequest):
    """Récupère les métadonnées et formats d'une vidéo via l'API."""
    try:
        media_info = MediaExtractor.extract(str(payload.url))
        return media_info
    except GetWayError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download", response_model=JobResponse)
def start_download(payload: APIDownloadRequest, background_tasks: BackgroundTasks):
    """Lance un téléchargement en arrière-plan et retourne un ID de suivi."""
    job_id = job_manager.create_job(payload)
    
    # Exécution asynchrone en arrière-plan pour ne pas bloquer la requête HTTP
    background_tasks.add_task(job_manager.run_download, job_id, payload)
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Téléchargement démarré en arrière-plan."
    )

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    """Permet de suivre l'état d'un téléchargement en cours."""
    job = job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable.")
    
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        message=f"Progression : {job.get('progress', 0.0)}%",
        file_path=job.get("file_path"),
        error=job.get("error")
    )