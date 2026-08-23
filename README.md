# Eloquent Miner — Frontend

React + Vite + Tailwind web UI for the [Eloquent Miner backend](../eloquent-miner).
Review mined phrases, listen to real speaker audio, edit clips, and export to Anki.

## Prerequisites

- Node.js 18+
- Backend running at `http://localhost:8000`

## Run

```bash
make up
```

That's it — installs dependencies and starts the dev server at `http://localhost:3000`.

Without make:

```bash
npm install
npm run dev
```

## Features

- Create jobs from YouTube URLs
- Review phrases with real speaker audio
- Approve / reject / edit / delete phrases
- Audio clip editor (trim, extend, preview, re-cut)
- One-click Anki export