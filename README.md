# Eloquent Miner(Backend)

Mine eloquent English phrases from YouTube videos and turn them into Anki flashcards with the **original speaker's voice**.

Paste a YouTube URL → backend downloads audio + subtitles → LLM extracts eloquent phrases (verified against the real transcript) → ffmpeg cuts real audio clips → export an `.apkg` deck with embedded audio. Includes a React web UI to review, edit clips, and export.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) — `winget install Gyan.FFmpeg`
- Deno — `winget install DenoLand.Deno` (required by yt-dlp for JavaScript execution)
- An LLM API key (Gemini, OpenRouter, OpenAI, Groq) or local Ollama

> Windows: after installing tools, open a **new** terminal so PATH refreshes.

## Run the Backend

```bash
cd eloquent-miner
uv venv
uv sync

# create config and add your LLM key
copy .env.example .env      # macOS/Linux: cp .env.example .env

make up
```

Backend runs at `http://localhost:8000` (Swagger at `/docs`).

Minimal `.env`:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.7-flash
LLM_API_KEY=your_api_key
```

## Frontend

The frontend is maintained in a separate repository:

[**Eloquent Frontend**](https://github.com/YusufKeremKezer/eloquent-frontend)