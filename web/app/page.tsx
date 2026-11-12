"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type MediaFormat = {
  format_id: string;
  ext: string;
  resolution?: string | null;
  fps?: number | null;
  filesize?: number | null;
  format_note?: string | null;
  vcodec?: string | null;
  acodec?: string | null;
};

type MediaInfo = {
  title: string;
  uploader?: string | null;
  duration?: number | null;
  thumbnail?: string | null;
  formats: MediaFormat[];
};

type Job = {
  job_id: string;
  status: "pending" | "extracting" | "downloading" | "processing" | "completed" | "failed" | "cancelled";
  progress: number;
  error?: string | null;
};

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production" ? "/api" : "http://127.0.0.1:8000")
).replace(/\/$/, "");

async function readError(response: Response) {
  try {
    const body = await response.json();
    return body.detail || body.message || "Une erreur est survenue.";
  } catch {
    return "Le service GetWay ne répond pas. Réessaie dans un instant.";
  }
}

function formatDuration(seconds?: number | null) {
  if (!seconds) return "Durée inconnue";
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}:${String(remaining).padStart(2, "0")}`;
}

function formatSize(bytes?: number | null) {
  if (!bytes) return "taille inconnue";
  return bytes > 1_000_000_000
    ? `${(bytes / 1_000_000_000).toFixed(1)} Go`
    : `${Math.round(bytes / 1_000_000)} Mo`;
}

const statusLabels: Record<Job["status"], string> = {
  pending: "Dans la file d’attente",
  extracting: "Analyse de la vidéo",
  downloading: "Téléchargement en cours",
  processing: "Préparation du fichier",
  completed: "Fichier prêt",
  failed: "Échec du téléchargement",
  cancelled: "Téléchargement annulé",
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [formatId, setFormatId] = useState("");
  const [audioOnly, setAudioOnly] = useState(false);
  const [audioFormat, setAudioFormat] = useState("mp3");
  const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const videoFormats = useMemo(() => {
    if (!media) return [];
    const seen = new Set<string>();
    return media.formats
      .filter((item) => item.ext && item.ext !== "mhtml" && item.vcodec !== "none" && item.acodec !== "none")
      .filter((item) => {
        const key = `${item.resolution || item.format_note || item.ext}-${item.ext}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .reverse()
      .slice(0, 18);
  }, [media]);

  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled"].includes(job.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/jobs/${job.job_id}`, { cache: "no-store" });
        if (!response.ok) throw new Error(await readError(response));
        const updated: Job = await response.json();
        setJob(updated);
        if (updated.status === "failed") setError(updated.error || "Le téléchargement a échoué.");
      } catch (pollError) {
        setError(pollError instanceof Error ? pollError.message : "Impossible de suivre le téléchargement.");
      }
    }, 1400);
    return () => window.clearInterval(timer);
  }, [job]);

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMedia(null);
    setJob(null);
    const cleanedUrl = url.trim();
    try {
      const parsed = new URL(cleanedUrl);
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error("Saisis une adresse web qui commence par http:// ou https://.");
    } catch (parseError) {
      setError(parseError instanceof Error && parseError.message.startsWith("Saisis") ? parseError.message : "Saisis une URL vidéo valide.");
      return;
    }

    setBusy(true);
    try {
      const response = await fetch(`${API_URL}/info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: cleanedUrl }),
      });
      if (!response.ok) throw new Error(await readError(response));
      setMedia(await response.json());
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Impossible d’analyser cette adresse.");
    } finally {
      setBusy(false);
    }
  }

  async function startDownload() {
    setError("");
    setBusy(true);
    try {
      const response = await fetch(`${API_URL}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), format_id: audioOnly ? null : formatId || null, audio_only: audioOnly, audio_format: audioFormat }),
      });
      if (!response.ok) throw new Error(await readError(response));
      const created = await response.json();
      setJob({ job_id: created.job_id, status: created.status, progress: created.progress || 0 });
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Le téléchargement n’a pas pu démarrer.");
    } finally {
      setBusy(false);
    }
  }

  const downloadUrl = job ? `${API_URL}/jobs/${job.job_id}/file` : "#";

  return (
    <main className="page-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <header className="topbar wrap">
        <a className="brand" href="#top" aria-label="GetWay, accueil">
          <span className="brand-mark"><span /></span>
          <span>getway<span className="brand-period">.</span></span>
        </a>
        <nav className="nav-links" aria-label="Navigation principale">
          <a href="#comment-ca-marche">Comment ça marche</a>
          <a href="#a-propos">À propos</a>
          <span className="status-chip"><i /> VERSION BÊTA</span>
        </nav>
        <a className="top-cta" href="#telecharger">Essayer GetWay <span>↗</span></a>
      </header>

      <section className="hero wrap" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> LE WEB, À TON RYTHME</div>
          <h1>Garde ce que<br />tu veux <span>revoir.</span></h1>
          <p className="hero-description">Colle un lien, choisis ton format, et récupère ta vidéo en quelques instants. Simple, direct, sans détour.</p>
          <div className="hero-proof">
            <span className="proof-icon">✳</span>
            <span>Pour tes contenus et ceux que tu as le droit de télécharger.</span>
          </div>
          <a className="scroll-cue" href="#telecharger"><span className="scroll-dot">↓</span> COMMENCER</a>
        </div>

        <div className="hero-art" aria-label="Aperçu de l’interface GetWay">
          <div className="art-orbit orbit-a" />
          <div className="art-orbit orbit-b" />
          <div className="art-star star-a">✳</div>
          <div className="art-star star-b">✳</div>
          <div className="floating-note note-top"><span className="note-icon">↗</span><span><b>Juste un lien</b><small>Et c’est parti</small></span></div>
          <div className="player-card">
            <div className="player-top"><span className="player-dots"><i /><i /><i /></span><span className="player-label">GETWAY PLAYER</span><span className="player-menu">···</span></div>
            <div className="player-visual">
              <div className="visual-sun" />
              <div className="visual-hill hill-back" />
              <div className="visual-hill hill-front" />
              <div className="play-button"><span>▶</span></div>
              <div className="visual-caption"><span>YOUR NEXT<br />FAVORITE</span><span className="caption-index">01 / 04</span></div>
            </div>
            <div className="player-bottom"><span><i className="sound-icon">⌁</i> Prêt à emporter</span><span className="player-time">02:48</span></div>
          </div>
          <div className="floating-note note-bottom"><span className="download-glyph">↓</span><span><b>MP4 · MP3</b><small>À toi de choisir</small></span><span className="note-check">✓</span></div>
          <div className="art-caption">COLLECTIONNE TES INSTANTS <span>—</span> 01</div>
        </div>
      </section>

      <section className="download-section wrap" id="telecharger">
        <div className="section-kicker"><span>01</span><span className="kicker-rule" /> LE TÉLÉCHARGEMENT</div>
        <div className="download-layout">
          <div className="download-intro">
            <h2>Un lien.<br /><span>Et c’est à toi.</span></h2>
            <p>GetWay trouve les formats disponibles et prépare ton fichier. Tu gardes le contrôle à chaque étape.</p>
            <div className="privacy-note"><span>◈</span><p><b>Pas de compte à créer.</b><br />Tes téléchargements restent privés.</p></div>
          </div>

          <div className="download-card">
            <div className="card-heading"><div><span className="card-overline">TA PROCHAINE VIDÉO</span><h3>On commence où ?</h3></div><span className="step-count">ÉTAPE <b>{media ? "02" : "01"}</b> / 02</span></div>
            <form onSubmit={analyze} className="url-form">
              <label htmlFor="video-url">Lien de la vidéo</label>
              <div className="url-field"><span className="link-icon">↗</span><input id="video-url" type="url" placeholder="https://exemple.com/ma-video" value={url} onChange={(event) => setUrl(event.target.value)} required /><button type="submit" disabled={busy}>{busy && !media ? <span className="spinner" /> : "Analyser le lien"}<span className="button-arrow">→</span></button></div>
              <p className="field-hint"><span>⌁</span> Colle l’adresse complète de la vidéo à récupérer.</p>
            </form>

            {media && <div className="media-result">
              <div className="media-summary">
                {media.thumbnail ? <img src={media.thumbnail} alt="" className="media-thumb" /> : <div className="media-thumb thumb-placeholder">▶</div>}
                <div className="media-copy"><span className="media-meta">{media.uploader || "VIDÉO DÉTECTÉE"} <i /> {formatDuration(media.duration)}</span><strong>{media.title}</strong></div>
                <span className="detected-check">✓</span>
              </div>
              <div className="format-switch" role="group" aria-label="Type de fichier">
                <button type="button" className={!audioOnly ? "selected" : ""} onClick={() => setAudioOnly(false)}><span className="format-icon">▣</span> Vidéo <small>MP4</small></button>
                <button type="button" className={audioOnly ? "selected" : ""} onClick={() => setAudioOnly(true)}><span className="format-icon">♫</span> Audio <small>MP3</small></button>
              </div>
              {!audioOnly && videoFormats.length > 0 && <label className="quality-label" htmlFor="quality">Qualité vidéo
                <select id="quality" value={formatId} onChange={(event) => setFormatId(event.target.value)}>
                  <option value="">Meilleure qualité disponible</option>
                  {videoFormats.map((format) => <option key={format.format_id} value={format.format_id}>{format.resolution || format.format_note || format.ext} · {format.ext.toUpperCase()} · {formatSize(format.filesize)}</option>)}
                </select>
              </label>}
              <button className="download-button" type="button" onClick={startDownload} disabled={busy || !!job && !["failed", "cancelled"].includes(job.status)}>{busy ? <><span className="spinner" /> Préparation…</> : <>Préparer mon téléchargement <span>↗</span></>}</button>
            </div>}

            {job && <div className={`job-panel ${job.status}`} aria-live="polite">
              <div className="job-line"><span className="job-indicator">{job.status === "completed" ? "✓" : job.status === "failed" ? "!" : <span className="spinner" />}</span><div className="job-copy"><strong>{statusLabels[job.status]}</strong><small>{job.status === "completed" ? "Ton fichier peut être téléchargé." : job.status === "failed" ? (job.error || error) : "Tu peux garder cette page ouverte pendant la préparation."}</small></div>{job.status === "downloading" && <b className="job-percent">{Math.round(job.progress)}%</b>}</div>
              {!['completed', 'failed', 'cancelled'].includes(job.status) && <div className="progress-track"><span style={{ width: `${Math.max(4, Math.min(100, job.progress))}%` }} /></div>}
              {job.status === "completed" && <a className="download-button file-link" href={downloadUrl}><span>↓</span> Télécharger le fichier <span>↗</span></a>}
            </div>}

            {error && <div className="error-message" role="alert"><span>!</span> {error}</div>}
            <div className="card-foot"><span>↗</span> Compatible avec de nombreuses plateformes vidéo</div>
          </div>
        </div>
      </section>

      <section className="how-section wrap" id="comment-ca-marche">
        <div className="section-kicker"><span>02</span><span className="kicker-rule" /> SANS MODE D’EMPLOI</div>
        <div className="how-heading"><h2>Trois petits gestes.<br /><span>Et c’est dans la poche.</span></h2><p>Pas de logiciel à installer.<br />Juste GetWay et ton lien.</p></div>
        <div className="steps-grid">
          <article className="step-card"><span className="step-number">01</span><div className="step-illustration link-illustration"><span>↗</span><i /><i /><i /></div><h3>Colle ton lien</h3><p>Copie l’adresse de la vidéo que tu souhaites garder.</p></article>
          <article className="step-card"><span className="step-number">02</span><div className="step-illustration format-illustration"><span>MP4</span><span>MP3</span><i>↔</i></div><h3>Choisis ton format</h3><p>Vidéo ou audio, sélectionne ce qui te convient.</p></article>
          <article className="step-card"><span className="step-number">03</span><div className="step-illustration ready-illustration"><span>↓</span><i>✓</i></div><h3>Récupère ton fichier</h3><p>Patiente un instant, puis télécharge ton fichier prêt.</p></article>
        </div>
      </section>

      <footer className="footer wrap" id="a-propos"><a className="brand" href="#top"><span className="brand-mark"><span /></span><span>getway<span className="brand-period">.</span></span></a><p>Garde ce que tu veux revoir.</p><span className="footer-legal">Utilise GetWay pour les contenus que tu possèdes ou que tu es autorisé à télécharger.</span><span className="footer-copy">© 2026 GETWAY</span></footer>
    </main>
  );
}
