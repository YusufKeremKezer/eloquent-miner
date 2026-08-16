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
    return any(re.match(pattern, url) for pattern in patterns)


def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_info(url: str) -> dict:
    # NO extra flags. Default client selection works best.
    cmd = [
        "yt-dlp",
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
        print(f"Failed to parse video info: {e}")
        print(f"First 500 chars: {first_line[:500]}")
        raise RuntimeError(f"Failed to parse video info: {e}")


def download_audio(url: str, output_dir: Path, video_id: str) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "source.%(ext)s")

    # Fallback chain: try formats in order until one succeeds.
    # 140 = m4a medium, 251 = webm opus, 18 = progressive mp4 (has audio)
    strategies = [
        ("bestaudio", ["-f", "bestaudio/best"]),
        ("140 (m4a audio)", ["-f", "140"]),
        ("251 (webm audio)", ["-f", "251"]),
        ("139 (m4a low)", ["-f", "139"]),
        ("18 (mp4 progressive)", ["-f", "18"]),
    ]

    last_error = ""

    for i, (name, fmt_args) in enumerate(strategies):
        cmd = [
            "yt-dlp",
            *fmt_args,
            "--extract-audio",
            "--audio-format", settings.youtube_audio_format,
            "--audio-quality", "0",
            "-o", output_template,
            "--no-playlist",
            url
        ]

        print(f"[{i+1}/{len(strategies)}] Trying format: {name}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            audio_file = output_dir / f"source.{settings.youtube_audio_format}"
            if audio_file.exists() and audio_file.stat().st_size > 1000:
                print(f"✅ Success with format: {name}")
                return str(audio_file)

        last_error = result.stderr
        print(f"❌ Failed with format: {name}")

    raise RuntimeError(f"Failed to download audio with all formats. Last error: {last_error}")


def download_subtitles(url: str, output_dir: Path, video_id: str) -> Optional[str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "subs")

    langs = settings.youtube_subtitle_langs.split(",")

    cmd = [
        "yt-dlp",
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
        print(f"Subtitle download warning: {result.stderr}")
        return None

    for lang in langs:
        for ext in ["srt", "vtt"]:
            sub_file = output_dir / f"subs.{lang}.{ext}"
            if sub_file.exists():
                print(f"Found subtitle: {sub_file}")
                return str(sub_file)

    for ext in ["srt", "vtt"]:
        for sub_file in output_dir.glob(f"subs*.{ext}"):
            if sub_file.exists():
                print(f"Found subtitle (fallback): {sub_file}")
                return str(sub_file)

    print("No subtitle file found")
    return None


def process_youtube_url(url: str, job_id: str) -> Tuple[str, Optional[str], dict]:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    job_media_dir = Path(settings.media_dir) / job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching video info...")
    video_info = get_video_info(url)

    print(f"Downloading audio...")
    audio_path = download_audio(url, job_media_dir, video_id)

    print(f"Downloading subtitles...")
    subtitle_path = download_subtitles(url, job_media_dir, video_id)

    return audio_path, subtitle_path, video_info