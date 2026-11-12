# 🚀 GetWay

**GetWay** est un moteur de téléchargement et d'extraction vidéo/audio moderne, modulaire et extensible écrit en Python. 

Conçu autour d'une architecture découplée, il permet d'utiliser un même cœur métier (`core`) à travers plusieurs interfaces : une ligne de commande ergonomique (**CLI**), une **API asynchrone** avec suivi en temps réel, et une future **extension navigateur** (Manifest V3).

---

## ✨ Fonctionnalités principales

- **Architecture découplée (`src/` layout) :** Le moteur central n'a aucune dépendance envers la CLI ou l'API.
- **Installation modulaire :** Installez uniquement ce dont vous avez besoin via les extras Python (`[cli]`, `[api]`).
- **Extraction rapide de métadonnées :** Récupération des titres, miniatures et formats disponibles sans déclencher le téléchargement.
- **Suivi de progression agnostique :** Système de callbacks basé sur des protocoles Python, compatible aussi bien avec les barres de progression terminal (`Rich`) que les flux temps réel web (`SSE` / `WebSockets`).
- **Post-traitement intégré :** Fusion vidéo/audio haute définition et extraction audio (MP3, etc.) pilotées par `FFmpeg`.
- **Sécurité locale :** Protection intégrée pour l'API locale (validation d'origine CORS et authentification par token pour l'extension).

---

## 📂 Architecture du projet

```text
getway/
├── pyproject.toml              # Configuration du package et gestion des extras ([cli], [api])
├── src/getway/
│   ├── core/                   # Cœur métier (zéro dépendance vers cli/ ou api/)
│   │   ├── models.py           # Modèles Pydantic (DownloadRequest, MediaInfo, JobStatus...)
│   │   ├── errors.py           # Hiérarchie d'exceptions (GetWayError -> ExtractionError, FFmpegError...)
│   │   ├── extractor.py        # Extraction des métadonnées via yt-dlp
│   │   ├── downloader.py       # Gestion du téléchargement et hooks de progression
│   │   ├── postprocess.py      # Conversions et fusions via FFmpeg
│   │   ├── progress.py         # Protocole ProgressCallback (agnostique du transport)
│   │   └── config.py           # Configuration centralisée (pydantic-settings)
│   ├── cli/
│   │   └── main.py             # Interface en ligne de commande (Typer + Rich)
│   └── api/
│       ├── app.py              # Application FastAPI, gestion du cycle de vie et CORS
│       ├── routes/             # Endpoints REST & temps réel (jobs.py, info.py, events.py)
│       ├── jobs/               # JobManager, file d'attente et gestion d'état
│       ├── schemas.py          # Schémas DTO de l'API
│       └── security.py         # Sécurisation des accès locaux (tokens, origines autorisées)
├── extension/                  # Extension navigateur Manifest V3 (à venir)
└── tests/                      # Suite de tests unitaires et d'intégration
```

---

## 🛠️ Prérequis

- **Python 3.11+**
- **FFmpeg** installé et accessible dans le `PATH` de votre système (indispensable pour la fusion des flux HD et l'extraction audio).

---

## 📦 Installation

Clonez le dépôt et installez le package selon votre usage :

```bash
git clone https://github.com/votre-utilisateur/getway.git
cd getway
```

### 1. Moteur Core uniquement (usage en tant que bibliothèque)
```bash
pip install -e .
```

### 2. Avec l'interface en ligne de commande (CLI)
```bash
pip install -e ".[cli]"
```

### 3. Avec le serveur API Backend
```bash
pip install -e ".[api]"
```

### 4. Installation complète (Développement)
```bash
pip install -e ".[cli,api]"
```

---

## 🚀 Utilisation

### Via la CLI
*(Exemples de commandes une fois la CLI implémentée)*

```bash
# Télécharger une vidéo dans la meilleure qualité disponible
getway download "https://exemple.com/video"

# Extraire uniquement la piste audio en MP3
getway download "https://exemple.com/video" --audio

# Obtenir les informations et formats disponibles sans télécharger
getway info "https://exemple.com/video"
```

### Via l'API Backend
Démarrez le serveur local avec `uvicorn` :

```bash
uvicorn getway.api.app:app --reload --host 127.0.0.1 --port 8000
```
La documentation interactive (Swagger UI) sera accessible à l'adresse : `http://127.0.0.1:8000/docs`.

---

## 🗺️ Feuille de route (Roadmap)

- [x] Définition de l'architecture et de l'arborescence modulaire
- [ ] Implémentation du moteur `core` (modèles, extracteur, téléchargeur, FFmpeg)
- [ ] Développement de l'interface `cli` avec Typer & Rich
- [ ] Développement de l'API `FastAPI` et du `JobManager` asynchrone
- [ ] Ajout du flux de progression temps réel (SSE / WebSockets)
- [ ] Création de l'extension navigateur (Chrome / Firefox - Manifest V3)
- [ ] Écriture des tests unitaires et d'intégration (`pytest`)

---

## ⚠️ Avertissement légal

**GetWay** est un outil développé à des fins éducatives et personnelles. Veuillez respecter les droits d'auteur ainsi que les conditions d'utilisation des plateformes sources. N'utilisez cet outil que pour télécharger des contenus libres de droits, vos propres créations ou des médias pour lesquels vous disposez d'une autorisation explicite.