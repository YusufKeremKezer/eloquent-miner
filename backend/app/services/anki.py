import hashlib
from pathlib import Path
from typing import Optional

import genanki
from sqlmodel import Session, select

from app.core.config import settings
from app.models.job import Job
from app.models.phrase import Phrase


def generate_anki_id(input_string: str) -> int:
    hash_val = int(hashlib.md5(input_string.encode()).hexdigest()[:8], 16)
    return hash_val


def format_timestamp(seconds: float) -> str:
    """123.4 -> '02:03' , 3725 -> '1:02:05'"""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def build_timestamped_url(url: str, start: Optional[float]) -> str:
    """
    Appends YouTube timestamp parameter so the video opens exactly
    at the moment the phrase is spoken.
    Works with both watch?v= and youtu.be links.
    """
    if not url:
        return ""
    if start is None:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}t={int(start)}s"


def build_anki_deck(session: Session, job: Job, status_filter: Optional[str] = None) -> str:
    statement = select(Phrase).where(Phrase.job_id == job.id)
    if status_filter:
        statement = statement.where(Phrase.status == status_filter)

    phrases = session.exec(statement).all()

    if not phrases:
        raise ValueError(f"No phrases found for job {job.id}")

    deck_id = generate_anki_id(f"deck_{job.id}")
    model_id = generate_anki_id(f"model_{job.id}")

    eloquent_model = genanki.Model(
        model_id,
        'Eloquent Phrase',
        fields=[
            {'name': 'Phrase'},
            {'name': 'Definition'},
            {'name': 'Usage'},
            {'name': 'ExampleOriginal'},
            {'name': 'ExampleNew'},
            {'name': 'Register'},
            {'name': 'Alternatives'},
            {'name': 'WhyEloquent'},
            {'name': 'Audio'},
            {'name': 'Source'},
        ],
        templates=[
            {
                'name': 'Eloquent Phrase',
                'qfmt': (
                    '<div style="font-size: 18px; color: #555;">'
                    '{{Definition}}'
                    '</div>'
                    '<br>'
                    '<div style="font-size: 14px; color: #888; font-style: italic;">'
                    '{{Usage}}'
                    '</div>'
                    '<br><br>'
                    '<div style="font-size: 16px;">'
                    '<i>What is the phrase?</i>'
                    '</div>'
                ),
                'afmt': (
                    '{{FrontSide}}'
                    '<hr id="answer">'
                    '<div style="font-size: 24px; font-weight: bold; color: #2c3e50;">'
                    '{{Phrase}}'
                    '</div>'
                    '<br>'
                    '{{Audio}}'
                    '<br>'
                    '<div style="font-size: 14px; color: #666;">'
                    '<b>Example:</b> {{ExampleNew}}'
                    '</div>'
                    '<br>'
                    '<div style="font-size: 13px; color: #999;">'
                    '<b>Alternatives:</b> {{Alternatives}}'
                    '</div>'
                    '<br><br>'
                    '{{Source}}'
                ),
            },
        ],
        css='''
        .card {
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 16px;
            text-align: center;
            color: #333;
            background-color: #fafafa;
            padding: 20px;
        }
        a { color: #3b82f6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        '''
    )

    deck_name = f"Eloquent Miner::{job.title or job.id}"
    deck = genanki.Deck(deck_id, deck_name)

    media_files = []

    for phrase in phrases:
        audio_field = ""
        if phrase.audio_filename:
            audio_basename = Path(phrase.audio_filename).name
            audio_field = f"[sound:{audio_basename}]"

            audio_path = Path(settings.media_dir) / phrase.audio_filename
            if audio_path.exists():
                media_files.append(str(audio_path))
            # Per-phrase timestamped source link
        phrase_url = build_timestamped_url(job.source_url or "", phrase.start)
        if phrase_url and phrase.start is not None:
            source_link = (
                f'<a href="{phrase_url}">'
                f'🎬 Watch in context ({format_timestamp(phrase.start)})'
                f'</a>'
            )
        elif phrase_url:
            source_link = f'<a href="{phrase_url}">🎬 Watch Source Video</a>'
        else:
            source_link = ""

        alternatives_str = ", ".join(phrase.alternatives) if phrase.alternatives else ""

        note = genanki.Note(
            model=eloquent_model,
            fields=[
                phrase.phrase or "",
                phrase.definition or "",
                phrase.usage or "",
                phrase.example_original or "",
                phrase.example_new or "",
                phrase.register or "",
                alternatives_str,
                phrase.why_eloquent or "",
                audio_field,
                source_link,
            ],
            tags=[settings.app_name.lower().replace(" ", "-"), "eloquence"]
        )
        deck.add_note(note)

    package = genanki.Package(deck)
    if media_files:
        package.media_files = media_files

    output_dir = Path(settings.jobs_dir) / job.id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"eloquent_miner_{job.id}.apkg"
    output_path = output_dir / output_filename

    package.write_to_file(str(output_path))

    return str(output_path)