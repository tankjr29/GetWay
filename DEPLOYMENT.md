# Déployer GetWay

Le dépôt contient deux services séparés : le site Next.js (`web/`) et l’API Python avec FFmpeg. Le site peut être déployé sur Vercel ; l’API doit tourner sur un service qui accepte un conteneur Docker.

## 1. Déployer l’API de téléchargement

Crée un service web Docker chez ton hébergeur (par exemple Render, Railway ou Fly.io), connecté au dépôt. Le `Dockerfile` est à la racine du projet. Le processus écoute sur le port fourni par la plateforme ; si elle exige une variable `$PORT`, configure sa commande de démarrage ainsi :

```sh
uvicorn getway.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
```

Configure ces variables dans le service :

| Variable | Valeur |
| --- | --- |
| `GETWAY_ALLOWED_ORIGINS` | URL Vercel, par exemple `https://getway.vercel.app` (plusieurs origines séparées par des virgules) |
| `GETWAY_DOWNLOAD_DIR` | Répertoire temporaire inscriptible, par exemple `/tmp/getway-downloads` |
| `GETWAY_MAX_CONCURRENT_DOWNLOADS` | Nombre de téléchargements simultanés, par exemple `2` |

FFmpeg est installé dans l’image Docker. Le point de contrôle est `https://<api-host>/health`.

## 2. Déployer le site sur Vercel

Importe le même dépôt dans Vercel et choisis `web` comme **Root Directory**. Vercel détectera Next.js. Ajoute cette variable avant le déploiement :

| Variable | Valeur |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | URL publique de l’API, sans slash final, par exemple `https://getway-api.example.com` |

Ajoute aussi l’URL Vercel à `GETWAY_ALLOWED_ORIGINS` dans le service API. Si tu ajoutes un domaine personnalisé, ajoute-le également à cette liste, puis redéploie l’API.

## 3. Démarrer en local

Dans un terminal à la racine :

```powershell
python -m pip install -e ".[api]"
uvicorn getway.api.app:app --reload
```

Dans un second terminal :

```powershell
cd web
npm install
npm run dev
```

Le site sera disponible sur `http://localhost:3000` et l’API sur `http://localhost:8000`. CORS autorise déjà `http://localhost:3000` en local.

## Limites de la première version

Les jobs et leurs fichiers sont conservés dans la mémoire et le stockage temporaire de l’instance API. Ils peuvent disparaître lors d’un redémarrage, et le suivi suppose une seule instance API. Avant d’ouvrir largement le service, ajoute un stockage d’objets durable avec des liens temporaires, une file de jobs partagée et une limite de requêtes par adresse. Configure aussi les règles d’usage et les plateformes que tu souhaites prendre en charge.
