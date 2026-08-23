import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings


def validate_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"(https?://)?(www\.)?youtu\.be/[\w-]{11}",
        r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}",
        r"(https?://)?(www\.)?youtube\.com/embed/[\w-]{11}",
    ]
    return any(re.match(p, url) for p in patterns)


def extract_video_id(url: str) -> Optional[str]:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", url)
    return m.group(1) if m else None


def get_video_info(url: str) -> dict:
    cmd = [
        "yt-dlp",
        "--js-runtimes", "deno",
        "--dump-json",
        "--no-download",
        "--no-playlist",
        url
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch video info: {result.stderr}")

    first_line = result.stdout.strip().split('\n')[0]
    try:
        return json.loads(first_line)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse video info: {e}")


def download_audio(url: str, output_dir: Path, video_id: str) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "source.%(ext)s")

    cmd = [
        "yt-dlp",
        "--js-runtimes", "deno",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", settings.youtube_audio_format,
        "--audio-quality", "0",
        "-o", output_template,
        "--no-playlist",
        url
    ]
    print(f"Downloading audio: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_msg = result.stderr

        if "Private video" in error_msg or "deleted" in error_msg.lower():
            raise RuntimeError("This video is private or has been deleted.")
        elif "Only images" in error_msg:
            raise RuntimeError("Slideshow/story video - no audio stream.")
        else:
            raise RuntimeError(f"Failed to download audio: {error_msg[:500]}")

    # Find downloaded file
    audio_file = output_dir / f"source.{settings.youtube_audio_format}"
    if audio_file.exists() and audio_file.stat().st_size > 1000:
        print(f"✅ Audio downloaded: {audio_file}")
        return str(audio_file)

    for ext in ["mp3", "wav", "m4a", "ogg", "flac", "webm"]:
        fallback = output_dir / f"source.{ext}"
        if fallback.exists():
            print(f"✅ Audio downloaded (fallback): {fallback}")
            return str(fallback)

    raise RuntimeError("Audio file was not created after download.")


def download_subtitles(url: str, output_dir: Path, video_id: str) -> Optional[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "subs")
    langs = settings.youtube_subtitle_langs.split(",")

    cmd = [
        "yt-dlp",
        "--js-runtimes", "deno",
        "--no-check-certificate",
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", ",".join(langs),
        "--sub-format", "srt/vtt/best",
        "--convert-subs", "srt",
        "-o", output_template,
        "--no-playlist",
        url
    ]
    print(f"Downloading subtitles: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Subtitle warning: {result.stderr[:300]}")
        return None

    for lang in langs:
        for ext in ["srt", "vtt"]:
            sub_file = output_dir / f"subs.{lang}.{ext}"
            if sub_file.exists():
                print(f"✅ Found subtitle: {sub_file}")
                return str(sub_file)

    for ext in ["srt", "vtt"]:
        for sub_file in output_dir.glob(f"subs*.{ext}"):
            if sub_file.exists():
                print(f"✅ Found subtitle (fallback): {sub_file}")
                return str(sub_file)

    print("⚠️ No subtitle file found")
    return None


def process_youtube_url(url: str, job_id: str) -> Tuple[str, Optional[str], dict]:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Invalid URL: {url}")

    job_media_dir = Path(settings.media_dir) / job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching video info...")
    video_info = get_video_info(url)

    print("Downloading audio...")
    audio_path = download_audio(url, job_media_dir, video_id)

    print("Downloading subtitles...")
    subtitle_path = download_subtitles(url, job_media_dir, video_id)

    return audio_path, subtitle_path, video_info