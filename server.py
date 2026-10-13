#!/usr/bin/env python3
import json
import mimetypes
import os
import re
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import yt_dlp

ROOT = Path(__file__).resolve().parent
DOWNLOADS = ROOT / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

for candidate in (
    r"C:\Users\penda\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin",
    r"C:\ffmpeg\bin",
):
    path = Path(candidate)
    if path.exists():
        os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")
        break

ALLOWED_FORMATS = {
    "mp3-320": {"codec": "mp3", "quality": "0"},
    "mp3-192": {"codec": "mp3", "quality": "2"},
    "m4a": {"codec": "m4a", "quality": "0"},
    "wav": {"codec": "wav", "quality": "0"},
    "mp4-1080": {"codec": "mp4", "quality": "1080p"},
    "mp4-720": {"codec": "mp4", "quality": "720p"},
    "mp4-4k": {"codec": "mp4", "quality": "4k"},
    "webm": {"codec": "webm", "quality": "best"},
}


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "-", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned[:80] or "download"
    return cleaned.replace(" ", "_")


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
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    allowed_hosts = ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "pinterest.com", "www.pinterest.com", "pin.it")
    if host not in allowed_hosts and not host.endswith(".youtube.com") and not host.endswith(".pinterest.com"):
        raise ValueError("URL non prise en charge. Utilisez uniquement un lien YouTube ou Pinterest valide.")
    return url


def build_download_options(url, format_key, title="download"):
    if format_key not in ALLOWED_FORMATS:
        raise ValueError(f"Format non supporté: {format_key}")

    config = ALLOWED_FORMATS[format_key]
    out_template = str(DOWNLOADS / f"{safe_name(title)}.%(ext)s")

    if format_key.startswith("mp3") or format_key in {"m4a", "wav"}:
        return {
            "format": "bestaudio/best",
            "noplaylist": True,
            "overwrite": True,
            "restrictfilenames": True,
            "no_warnings": True,
            "quiet": True,
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": config["codec"],
                "preferredquality": config["quality"],
            }],
        }

    if format_key == "webm":
        return {
            "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best",
            "merge_output_format": "webm",
            "noplaylist": True,
            "overwrite": True,
            "restrictfilenames": True,
            "no_warnings": True,
            "quiet": True,
            "outtmpl": out_template,
        }

    return {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "overwrite": True,
        "restrictfilenames": True,
        "no_warnings": True,
        "quiet": True,
        "outtmpl": out_template,
    }


def maybe_find_downloaded_file(prefix: str, extension_hint: str | None = None) -> str | None:
    candidates = []
    for file in DOWNLOADS.iterdir():
        if not file.is_file():
            continue
        name = file.name
        if name.startswith(prefix) and not name.endswith(".tmp") and not name.endswith(".part"):
            if extension_hint and not name.endswith(extension_hint):
                continue
            candidates.append(file)

    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime).name


def extract_media(url: str, format_key: str):
    ensure_allowed_url(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("Aucune métadonnée valide n’a été retournée par la source.")

    if "entries" in info:
        info = info["entries"][0]

    title = info.get("title") or "Téléchargement"
    thumbnail = info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url")
    duration = info.get("duration")
    platform_name = "YouTube" if "youtube" in (urlparse(url).netloc or "").lower() else "Pinterest"

    prefix = safe_name(title)
    ydl_options = build_download_options(url, format_key, title)
    file_name = maybe_find_downloaded_file(prefix)
    if file_name and file_name.endswith((".mp3", ".mp4", ".m4a", ".wav", ".webm")):
        # Clean stale outputs when the same title is requested again.
        for existing in DOWNLOADS.iterdir():
            if existing.name.startswith(prefix) and existing.is_file():
                existing.unlink(missing_ok=True)

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        ydl.download([url])

    file_name = None
    if format_key.startswith("mp3") or format_key in {"m4a", "wav"}:
        file_name = maybe_find_downloaded_file(prefix, ".mp3" if format_key.startswith("mp3") else (".m4a" if format_key == "m4a" else ".wav"))
    elif format_key == "webm":
        file_name = maybe_find_downloaded_file(prefix, ".webm")
    else:
        file_name = maybe_find_downloaded_file(prefix, ".mp4")

    if not file_name:
        # Fallback: use the newest candidate in the download folder.
        candidates = [p.name for p in DOWNLOADS.iterdir() if p.is_file() and p.name.startswith(prefix)]
        if not candidates:
            raise ValueError("Le téléchargement n’a pas généré de fichier exploitable.")
        file_name = max(candidates)

    file_path = DOWNLOADS / file_name
    if not file_path.exists() or file_path.stat().st_size <= 0:
        raise ValueError("Le fichier généré est vide ou introuvable.")

    return {
        "title": title,
        "author": info.get("uploader") or info.get("channel") or "Source inconnue",
        "thumb": thumbnail or "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=900",
        "duration": readable_duration(duration),
        "platformName": platform_name,
        "downloadUrl": f"/download/{file_name}",
        "videoStreamUrl": f"/download/{file_name}",
        "audioStreamUrl": f"/download/{file_name}",
        "format": format_key,
    }


class FlexTubeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/download":
            self.send_error(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            if not raw:
                raise ValueError("Corps vide. Envoyez une URL et un format.")
            payload = json.loads(raw.decode("utf-8"))
            url = payload.get("url", "").strip()
            format_key = payload.get("format") or "mp3-320"
            if not url:
                raise ValueError("URL manquante.")
            result = extract_media(url, format_key)
            self.send_json({"ok": True, **result})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"ok": True, "status": "running"})
            return

        if parsed.path.startswith("/download/"):
            filename = unquote(parsed.path.split("/download/", 1)[1])
            safe = Path(filename).name
            if safe in {"", ".", ".."} or "/" in safe:
                self.send_error(400, "Invalid file name")
                return
            file_path = DOWNLOADS / safe
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "File not found")
                return
            mime, _ = mimetypes.guess_type(file_path.name)
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(file_path.stat().st_size))
            self.end_headers()
            with file_path.open("rb") as fh:
                shutil.copyfileobj(fh, self.wfile)
            return

        self.send_error(404, "Not found")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), FlexTubeHandler)
    print("FlexTube backend running at http://localhost:8000")
    server.serve_forever()
