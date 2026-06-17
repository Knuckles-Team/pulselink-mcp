"""Media backends: YouTube (yt-dlp) + podcast transcription (Whisper).

CONCEPT:PULSE-005 — Audio/video sources with transcript extraction
"""

from __future__ import annotations

from .base import CapabilityUnsupported, PulseDocument, PulseResult, SourceBackend


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
        url = url_or_id
        if "://" not in url:
            url = f"https://www.youtube.com/watch?v={url}"
        opts = {}
        if want_transcript:
            opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en", "en-US", "en-orig"],
            }
        with self._ydl(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        text = info.get("description", "") if info else ""
        if want_transcript and info:
            transcript = _extract_subtitle_text(info)
            if transcript:
                text = transcript
        return PulseDocument(
            id=(info or {}).get("id", url),
            url=url,
            title=(info or {}).get("title", ""),
            text=text,
            author=(info or {}).get("uploader", ""),
            created_at=(info or {}).get("upload_date", ""),
            metrics={
                "views": (info or {}).get("view_count") or 0,
                "duration": (info or {}).get("duration") or 0,
            },
        )


def _extract_subtitle_text(info: dict) -> str:
    """Download and flatten the best available English caption track to text."""
    import requests

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
            raw = requests.get(chosen["url"], timeout=30).text
        except Exception:  # nosec B112  # noqa: BLE001 - best-effort: skip a caption track that fails to download and try the next language
            continue
        return _strip_caption_markup(raw, chosen.get("ext", ""))
    return ""


def _strip_caption_markup(raw: str, ext: str) -> str:
    import json
    import re

    if ext == "json3":
        try:
            data = json.loads(raw)
            words = []
            for event in data.get("events", []):
                for seg in event.get("segs", []) or []:
                    words.append(seg.get("utf8", ""))
            return "".join(words).strip()
        except json.JSONDecodeError:
            return raw
    # VTT/SRT: drop timestamps + cue numbers.
    lines = []
    for line in raw.splitlines():
        if "-->" in line or line.strip().isdigit() or line.startswith("WEBVTT"):
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


class PodcastBackend(SourceBackend):
    """Podcast audio → transcript via local Whisper (``faster-whisper``).

    Keyless and server-side: downloads the episode audio and transcribes it. The
    heavy ASR dependency is lazy-imported and optional.
    """

    name = "whisper"

    def transcribe(self, url_or_id: str) -> PulseDocument:
        import tempfile

        import requests

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dep
            raise CapabilityUnsupported(
                "faster-whisper not installed — install pulselink-mcp[audio]"
            ) from exc
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=True) as fh:
            audio = requests.get(url_or_id, timeout=120, stream=True)
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
