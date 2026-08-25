# Eloquent Miner

Mine eloquent English phrases from YouTube videos and turn them into Anki flashcards with the **original speaker's voice**.

Paste a YouTube URL → download audio + subtitles → LLM extracts eloquent phrases (verified against the real transcript) → ffmpeg cuts real audio clips → export an `.apkg` deck with embedded audio. Includes a React web UI to review, edit clips, and export.

## Backend

FastAPI + SQLite + ffmpeg + yt-dlp.

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) — `winget install Gyan.FFmpeg`
- Deno — `winget install DenoLand.Deno` (required by yt-dlp for JavaScript execution)
- An LLM API key (Gemini, OpenRouter, OpenAI, Groq) or local Ollama

> Windows: after installing tools, open a **new** terminal so PATH refreshes.

### Run

```bash
cd backend
uv venv
uv sync

# create config and add your LLM key
copy .env.example .env      # macOS/Linux: cp .env.example .env

uv run python run.py
```

Runs at `http://localhost:8000` (Swagger at `/docs`).

Minimal `backend/.env`:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.7-flash
LLM_API_KEY=your_api_key
```

## Frontend

React + Vite + Tailwind. Review mined phrases, listen to real speaker audio, edit clips, and export to Anki.

### Prerequisites

- Node.js 18+
- Backend running at `http://localhost:8000`

### Run

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Features

- Create jobs from YouTube URLs
- Review phrases with real speaker audio
- Edit / delete phrases
- Audio clip editor (trim, extend, preview, re-cut)
- One-click Anki export