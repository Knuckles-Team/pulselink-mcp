"""Media backends: YouTube (yt-dlp) + podcast transcription (Whisper).

CONCEPT:PK-OS.governance.audio-video-sources-transcript — Audio/video sources with transcript extraction
"""

from __future__ import annotations

from .base import (
    CapabilityUnsupported,
    PulseDocument,
    PulseResult,
    SourceBackend,
)
from .http_transport import configured_session


class YouTubeBackend(SourceBackend):
    """YouTube search + transcript/metadata extraction via ``yt-dlp`` (keyless).

    Uses yt-dlp as a library (no external binary). ``search`` runs a
    ``ytsearchN`` query with flat extraction; ``fetch``/``transcribe`` pull video
    metadata and the best available subtitle/caption track as text.
    """

    name = "yt-dlp"

    def _ydl(self, opts: dict):
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:  # pragma: no cover - optional dep
            raise CapabilityUnsupported(
                "yt-dlp not installed — install pulselink-mcp[youtube]"
            ) from exc
        base = {"quiet": True, "no_warnings": True, "skip_download": True}
        base.update(opts)
        return YoutubeDL(base)

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        with self._ydl({"extract_flat": True}) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        docs: list[PulseDocument] = []
        for entry in (info or {}).get("entries", []) or []:
            vid = entry.get("id", "")
            docs.append(
                PulseDocument(
                    id=vid,
                    url=entry.get("url") or f"https://www.youtube.com/watch?v={vid}",
                    title=entry.get("title", ""),
                    author=entry.get("uploader") or entry.get("channel", ""),
                    metrics={"views": entry.get("view_count") or 0},
                )
            )
        return PulseResult(documents=docs)

    def fetch(self, url_or_id: str) -> PulseDocument:
        return self._extract(url_or_id, want_transcript=True)

    def transcribe(self, url_or_id: str) -> PulseDocument:
        return self._extract(url_or_id, want_transcript=True)

    def _extract(self, url_or_id: str, want_transcript: bool) -> PulseDocument:
        url = _normalize_youtube_url(url_or_id)
        opts = _transcript_ydl_opts() if want_transcript else {}
        with self._ydl(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        text = _resolve_youtube_text(info, want_transcript)
        return PulseDocument(**_youtube_document_fields(info, url, text))


def _normalize_youtube_url(url_or_id: str) -> str:
    """Turn a bare video id into a full watch URL; pass a real URL through."""
    if "://" not in url_or_id:
        return f"https://www.youtube.com/watch?v={url_or_id}"
    return url_or_id


def _transcript_ydl_opts() -> dict:
    """yt-dlp options requesting subtitle/caption tracks (manual + auto)."""
    return {
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "en-US", "en-orig"],
    }


def _resolve_youtube_text(info: dict | None, want_transcript: bool) -> str:
    """Prefer the flattened transcript when requested and available, else the description."""
    text = info.get("description", "") if info else ""
    if want_transcript and info:
        transcript = _extract_subtitle_text(info)
        if transcript:
            text = transcript
    return text


def _youtube_document_fields(info: dict | None, url: str, text: str) -> dict:
    """Build the PulseDocument kwargs for one extracted video."""
    info = info or {}
    return {
        "id": info.get("id", url),
        "url": url,
        "title": info.get("title", ""),
        "text": text,
        "author": info.get("uploader", ""),
        "created_at": info.get("upload_date", ""),
        "metrics": {
            "views": info.get("view_count") or 0,
            "duration": info.get("duration") or 0,
        },
    }


def _extract_subtitle_text(info: dict) -> str:
    """Download and flatten the best available English caption track to text."""
    tracks: dict[str, list[dict[str, str]]] = {}
    tracks.update(info.get("subtitles") or {})
    tracks.update(info.get("automatic_captions") or {})
    for lang in ("en", "en-US", "en-orig"):
        fmts = tracks.get(lang)
        if not fmts:
            continue
        chosen = next(
            (f for f in fmts if f.get("ext") in ("json3", "vtt", "srv1")), fmts[0]
        )
        try:
            raw = configured_session().get(chosen["url"], timeout=30).text
        except Exception:  # nosec B112  # noqa: BLE001 - best-effort: skip a caption track that fails to download and try the next language
            continue
        return _strip_caption_markup(raw, chosen.get("ext", ""))
    return ""


def _flatten_json3_captions(raw: str) -> str:
    """Flatten a yt-dlp ``json3`` caption track's word segments into plain text."""
    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    words = []
    for event in data.get("events", []):
        for seg in event.get("segs", []) or []:
            words.append(seg.get("utf8", ""))
    return "".join(words).strip()


def _strip_vtt_markup(raw: str) -> str:
    """Drop VTT/SRT timestamps, cue numbers, and inline tags, keeping only text."""
    import re

    lines = []
    for line in raw.splitlines():
        if "-->" in line or line.strip().isdigit() or line.startswith("WEBVTT"):
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _strip_caption_markup(raw: str, ext: str) -> str:
    if ext == "json3":
        return _flatten_json3_captions(raw)
    return _strip_vtt_markup(raw)


class PodcastBackend(SourceBackend):
    """Podcast audio → transcript via local Whisper (``faster-whisper``).

    Keyless and server-side: downloads the episode audio and transcribes it. The
    heavy ASR dependency is lazy-imported and optional.
    """

    name = "whisper"

    def transcribe(self, url_or_id: str) -> PulseDocument:
        import tempfile

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dep
            raise CapabilityUnsupported(
                "faster-whisper not installed — install pulselink-mcp[audio]"
            ) from exc
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=True) as fh:
            audio = configured_session().get(url_or_id, timeout=120, stream=True)
            audio.raise_for_status()
            for chunk in audio.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
            fh.flush()
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(fh.name)
            text = " ".join(seg.text for seg in segments).strip()
        return PulseDocument(id=url_or_id, url=url_or_id, text=text)

    def fetch(self, url_or_id: str) -> PulseDocument:
        return self.transcribe(url_or_id)
