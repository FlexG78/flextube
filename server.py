#!/usr/bin/env python3
import json
import logging
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import time
import uuid
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import yt_dlp

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("flextube")

DOWNLOADS = Path(os.environ.get("FLEXTUBE_DOWNLOAD_DIR", Path(tempfile.gettempdir()) / "flextube-downloads"))
DOWNLOADS.mkdir(parents=True, exist_ok=True)
PORT = int(os.environ.get("PORT", "8000"))
MAX_REQUEST_BYTES = 16 * 1024
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024
MAX_DURATION_SECONDS = 60 * 60
MAX_WAV_DURATION_SECONDS = 10 * 60
DOWNLOAD_TTL_SECONDS = 60 * 60
MAX_CONCURRENT_DOWNLOADS = 2
MAX_REQUESTS_PER_MINUTE = 20
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "FLEXTUBE_ALLOWED_ORIGINS",
        "https://flexg78.github.io,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
}
DOWNLOAD_SLOTS = threading.BoundedSemaphore(MAX_CONCURRENT_DOWNLOADS)
RATE_LOCK = threading.Lock()
REQUEST_TIMESTAMPS = deque()

ALLOWED_FORMATS = {
    "mp3-320": {"codec": "mp3", "quality": "0"},
    "mp3-192": {"codec": "mp3", "quality": "2"},
    "m4a": {"codec": "m4a", "quality": "0"},
    "wav": {"codec": "wav", "quality": "0"},
    "mp4-1080": {"codec": "mp4", "height": 1080},
    "mp4-720": {"codec": "mp4", "height": 720},
    "mp4-4k": {"codec": "mp4", "height": 2160},
    "webm": {"codec": "webm"},
}


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "-", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return (cleaned[:80] or "download").replace(" ", "_")


def readable_duration(seconds):
    if seconds is None:
        return "00:00"
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def ensure_allowed_url(url: str) -> str:
    if not isinstance(url, str) or not url or len(url) > 2048:
        raise ValueError("URL manquante ou trop longue.")

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 80, 443}
    ):
        raise ValueError("URL invalide. Utilisez un lien public YouTube ou Pinterest.")

    is_youtube = hostname in {"youtu.be"} or hostname == "youtube.com" or hostname.endswith(".youtube.com")
    is_pinterest = hostname in {"pin.it"} or hostname == "pinterest.com" or hostname.endswith(".pinterest.com")
    if not (is_youtube or is_pinterest):
        raise ValueError("URL non prise en charge. Utilisez uniquement un lien YouTube ou Pinterest valide.")

    path = parsed.path.rstrip("/")
    if is_youtube:
        if hostname == "youtu.be":
            valid_path = bool(re.fullmatch(r"/[A-Za-z0-9_-]{11}", path))
        else:
            video_id = r"[A-Za-z0-9_-]{11}"
            valid_path = path == "/watch" and bool(re.fullmatch(video_id, parse_qs(parsed.query).get("v", [""])[0]))
            valid_path = valid_path or bool(re.fullmatch(rf"/(?:shorts|live|embed|v)/{video_id}", path))
            valid_path = valid_path or bool(re.fullmatch(r"/clip/[A-Za-z0-9_-]{10,80}", path))
        if not valid_path:
            raise ValueError("URL YouTube invalide. Utilisez un lien vidéo ou Shorts.")
    elif hostname == "pin.it":
        if not re.fullmatch(r"/[A-Za-z0-9_-]{4,64}", path):
            raise ValueError("URL Pinterest invalide. Utilisez un lien de Pin.")
    elif not re.fullmatch(r"/pin/[0-9]+", path):
        raise ValueError("URL Pinterest invalide. Utilisez un lien de Pin.")
    return url


def build_download_options(format_key, output_template):
    if format_key not in ALLOWED_FORMATS:
        raise ValueError(f"Format non supporté : {format_key}")

    config = ALLOWED_FORMATS[format_key]
    common = {
        "noplaylist": True,
        "overwrites": True,
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 1,
        "fragment_retries": 1,
        "extractor_retries": 1,
        "file_access_retries": 1,
        "max_filesize": MAX_DOWNLOAD_BYTES,
        "outtmpl": output_template,
    }

    if format_key.startswith("mp3") or format_key in {"m4a", "wav"}:
        common["format"] = "bestaudio/best"
        common["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": config["codec"],
            "preferredquality": config["quality"],
        }]
        return common

    if format_key == "webm":
        common["format"] = "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]"
        common["merge_output_format"] = "webm"
        return common

    height = config["height"]
    common["format"] = (
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
        f"/best[height<={height}][ext=mp4]"
    )
    common["merge_output_format"] = "mp4"
    return common


def cleanup_expired_downloads():
    cutoff = time.time() - DOWNLOAD_TTL_SECONDS
    for directory in DOWNLOADS.iterdir():
        try:
            if directory.is_dir() and directory.stat().st_mtime < cutoff:
                shutil.rmtree(directory)
        except FileNotFoundError:
            continue
        except OSError:
            logger.exception("Could not remove expired download directory")


def acquire_rate_slot():
    now = time.monotonic()
    with RATE_LOCK:
        while REQUEST_TIMESTAMPS and REQUEST_TIMESTAMPS[0] <= now - 60:
            REQUEST_TIMESTAMPS.popleft()
        if len(REQUEST_TIMESTAMPS) >= MAX_REQUESTS_PER_MINUTE:
            return max(1, int(60 - (now - REQUEST_TIMESTAMPS[0])))
        REQUEST_TIMESTAMPS.append(now)
        return 0


def extract_media(url: str, format_key: str):
    ensure_allowed_url(url)
    if format_key not in ALLOWED_FORMATS:
        raise ValueError(f"Format non supporté : {format_key}")

    job_id = uuid.uuid4().hex
    job_dir = DOWNLOADS / job_id
    job_dir.mkdir(mode=0o700)
    output_template = str(job_dir / "media.%(ext)s")

    metadata_options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 1,
        "extractor_retries": 1,
    }
    try:
        with yt_dlp.YoutubeDL(metadata_options) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info or info.get("_type") == "playlist" or info.get("entries"):
            raise ValueError("Les playlists ne sont pas prises en charge. Utilisez le lien d’une vidéo ou d’un Pin.")

        duration = info.get("duration")
        if duration is not None and duration > MAX_DURATION_SECONDS:
            raise ValueError("Ce média dépasse la durée maximale autorisée (60 minutes).")
        if format_key == "wav" and duration is not None and duration > MAX_WAV_DURATION_SECONDS:
            raise ValueError("La conversion WAV est limitée aux médias de 10 minutes maximum.")

        download_options = build_download_options(format_key, output_template)
        def enforce_download_size(progress):
            if progress.get("downloaded_bytes", 0) > MAX_DOWNLOAD_BYTES:
                raise yt_dlp.utils.DownloadError("Le média dépasse la limite de taille autorisée (200 Mo).")

        download_options["progress_hooks"] = [enforce_download_size]
        with yt_dlp.YoutubeDL(download_options) as ydl:
            ydl.download([url])

        files = [
            path for path in job_dir.iterdir()
            if path.is_file() and not path.name.endswith((".part", ".ytdl", ".temp"))
        ]
        if len(files) != 1:
            raise ValueError("Le téléchargement n’a pas généré un fichier exploitable.")

        media_file = files[0]
        file_size = media_file.stat().st_size
        if file_size <= 0:
            raise ValueError("Le fichier généré est vide.")
        if file_size > MAX_DOWNLOAD_BYTES:
            raise ValueError("Le fichier dépasse la limite de taille autorisée (200 Mo).")

        title = info.get("title") or "Téléchargement"
        named_file = job_dir / f"{safe_name(title)}{media_file.suffix.lower()}"
        media_file.rename(named_file)
        media_file = named_file
        hostname = (urlparse(url).hostname or "").lower()
        platform_name = "YouTube" if hostname == "youtu.be" or hostname.endswith(".youtube.com") or hostname == "youtube.com" else "Pinterest"
        download_url = f"/download/{job_id}/{quote(media_file.name)}"
        return {
            "title": title,
            "author": info.get("uploader") or info.get("channel") or "Source inconnue",
            "thumb": info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url") or "",
            "duration": readable_duration(duration),
            "platformName": platform_name,
            "downloadUrl": download_url,
            "videoStreamUrl": download_url,
            "audioStreamUrl": download_url,
            "format": format_key,
            "fileSizeBytes": file_size,
        }
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise


class FlexTubeHandler(BaseHTTPRequestHandler):
    server_version = "FlexTube"

    def log_message(self, format, *args):
        logger.info("%s - %s", self.client_address[0], format % args)

    def origin_is_allowed(self):
        origin = self.headers.get("Origin")
        return not origin or origin.rstrip("/") in ALLOWED_ORIGINS

    def add_cors_headers(self):
        origin = self.headers.get("Origin")
        if origin and origin.rstrip("/") in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def send_json(self, payload, status=200, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        if not self.origin_is_allowed():
            self.send_json({"ok": False, "error": "Origine non autorisée."}, 403)
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.add_cors_headers()
        self.end_headers()

    def do_POST(self):
        if not self.origin_is_allowed():
            self.send_json({"ok": False, "error": "Origine non autorisée."}, 403)
            return
        if urlparse(self.path).path != "/api/download":
            self.send_json({"ok": False, "error": "Route introuvable."}, 404)
            return

        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self.send_json({"ok": False, "error": "Le type de contenu doit être application/json."}, 415)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"ok": False, "error": "Taille de requête invalide."}, 400)
            return
        if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
            self.send_json({"ok": False, "error": "Requête vide ou trop volumineuse."}, 413)
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Le corps JSON doit être un objet.")
            url = payload.get("url")
            format_key = payload.get("format", "mp3-320")
            if not isinstance(url, str) or not url.strip():
                raise ValueError("URL manquante.")
            if not isinstance(format_key, str):
                raise ValueError("Format invalide.")
            ensure_allowed_url(url.strip())
            if format_key not in ALLOWED_FORMATS:
                raise ValueError(f"Format non supporté : {format_key}")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)
            return

        retry_after = acquire_rate_slot()
        if retry_after:
            self.send_json(
                {"ok": False, "error": "Trop de demandes. Réessayez dans une minute."},
                429,
                {"Retry-After": str(retry_after)},
            )
            return

        if not DOWNLOAD_SLOTS.acquire(blocking=False):
            self.send_json({"ok": False, "error": "Le service est occupé. Réessayez dans quelques instants."}, 429)
            return

        cleanup_expired_downloads()
        try:
            result = extract_media(url.strip(), format_key)
            self.send_json({"ok": True, **result})
        except ValueError as exc:
            logger.info("Rejected media request: %s", exc)
            self.send_json({"ok": False, "error": str(exc)}, 400)
        except Exception:
            logger.exception("Media extraction failed")
            self.send_json(
                {"ok": False, "error": "La plateforme n’a pas permis de traiter ce média. Vérifiez le lien public et réessayez."},
                502,
            )
        finally:
            DOWNLOAD_SLOTS.release()

    def do_GET(self):
        if not self.origin_is_allowed():
            self.send_json({"ok": False, "error": "Origine non autorisée."}, 403)
            return

        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"ok": True, "status": "running"})
            return

        match = re.fullmatch(r"/download/([0-9a-f]{32})/([A-Za-z0-9_.-]+)", unquote(parsed.path))
        if match:
            job_id, filename = match.groups()
            job_dir = DOWNLOADS / job_id
            file_path = job_dir / filename
            if not file_path.is_file() or file_path.parent != job_dir:
                self.send_json({"ok": False, "error": "Fichier introuvable ou expiré."}, 404)
                return

            mime, _ = mimetypes.guess_type(filename)
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name(Path(filename).stem)}{Path(filename).suffix}"')
            self.send_header("Content-Length", str(file_path.stat().st_size))
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.add_cors_headers()
            self.end_headers()
            try:
                with file_path.open("rb") as media:
                    shutil.copyfileobj(media, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                logger.info("Client disconnected during download")
            return

        self.send_json({"ok": False, "error": "Route introuvable."}, 404)


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg est requis mais introuvable dans le PATH.")
    cleanup_expired_downloads()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), FlexTubeHandler)
    server.daemon_threads = True
    logger.info("FlexTube backend listening on port %s", PORT)
    server.serve_forever()
