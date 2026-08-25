import { useEffect, useState } from 'react';
import type { Job, Phrase } from '../types';
import {
  getPhrases,
  extractPhrases,
  generateClips,
  getExportUrl,
} from '../api/client';
import PhraseCard from '../components/PhraseCard';

interface Props {
  job: Job;
  onBack: () => void;
}

type StepState = 'locked' | 'active' | 'done';

interface StepCardProps {
  number: number;
  title: string;
  description: string;
  state: StepState;
  color: 'blue' | 'purple' | 'green';
  busy?: boolean;
  actionLabel: string;
  busyLabel?: string;
  onAction?: () => void;
  href?: string;
  disabled?: boolean;
  note?: string;
}

function StepCard({
  number, title, description, state, color,
  busy, actionLabel, busyLabel, onAction, href, disabled, note,
}: StepCardProps) {
  const boxStyles =
    state === 'done' ? 'border-green-300 bg-green-50' :
    state === 'active' ? 'border-blue-300 bg-blue-50' :
    'border-gray-200 bg-gray-50 opacity-60';

  const btnColor =
    color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' :
    color === 'purple' ? 'bg-purple-600 hover:bg-purple-700' :
    'bg-green-600 hover:bg-green-700';

  const badge = state === 'done' ? '✅' : state === 'locked' ? '🔒' : '👉';

  const btn = `${btnColor} px-4 py-2 rounded-lg text-white text-sm text-center disabled:opacity-50 disabled:cursor-not-allowed`;

  return (
    <div className={`border rounded-xl p-4 flex flex-col ${boxStyles}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-gray-700">Step {number}: {title}</div>
        <span>{badge}</span>
      </div>
      <p className="text-xs text-gray-500 mb-4 flex-1">{description}</p>

      {href ? (
        <a
          href={disabled ? undefined : href}
          download
          className={`${btn} ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
        >
          {actionLabel}
        </a>
      ) : (
        <button onClick={onAction} disabled={disabled || busy} className={btn}>
          {busy ? busyLabel : actionLabel}
        </button>
      )}

      {note && <p className="mt-2 text-[11px] text-gray-500">{note}</p>}
    </div>
  );
}

export default function JobDetailPage({ job, onBack }: Props) {
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [clipping, setClipping] = useState(false);

  // silent = true → listeyi "Loading"e çevirme, scroll zıplaması olmaz
  const fetchPhrases = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await getPhrases(job.id);
      setPhrases(data);
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhrases();
  }, [job.id]);

  const hasPhrases = phrases.length > 0;
  const hasClips = phrases.some((p) => p.audio_filename);
  const busy = extracting || clipping;

  const handleExtract = async () => {
    setExtracting(true);
    try {
      await extractPhrases(job.id);
      await fetchPhrases();
    } catch (err: any) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleClips = async () => {
    setClipping(true);
    try {
      await generateClips(job.id);
      await fetchPhrases(true); // silent: liste çökmez, scroll atmaz
    } catch (err: any) {
      alert(`Clipping failed: ${err.message}`);
    } finally {
      setClipping(false);
    }
  };

  // Lokal güncelleme: reload yok, scroll yok
  const handleUpdate = (updated: Phrase) => {
    setPhrases((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  };

  const handleDelete = (phrase: Phrase) => {
    setPhrases((prev) => prev.filter((p) => p.id !== phrase.id));
  };

  // Step states
  const step1: StepState = hasPhrases ? 'done' : 'active';
  const step2: StepState = !hasPhrases ? 'locked' : hasClips ? 'done' : 'active';
  const step3: StepState = !hasClips ? 'locked' : 'active';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={onBack} className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
        ← Back to Jobs
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{job.title || 'Untitled Job'}</h1>
        <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">{job.status}</span>
          <span>{phrases.length} phrases</span>
        </div>
        {job.source_url && (
          <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-sm text-blue-600 hover:text-blue-800">
            🎬 Watch Source Video
          </a>
        )}
      </div>

      {/* ── Pipeline steps ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
        <StepCard
          number={1}
          title="Extract Phrases"
          description="LLM mines eloquent phrases from the transcript (verified verbatim)."
          state={step1}
          color="blue"
          busy={extracting}
          actionLabel={hasPhrases ? '🧠 Re-extract' : '🧠 Extract Phrases'}
          busyLabel="Extracting..."
          onAction={handleExtract}
          disabled={busy || hasClips}
          note={
            hasClips
              ? 'Phrases already extracted. Use 📝 Edit Phrase on a card to modify it.'
              : undefined
          }
        />

        <StepCard
          number={2}
          title="Generate Clips"
          description="ffmpeg cuts the real speaker audio for each phrase."
          state={step2}
          color="purple"
          busy={clipping}
          actionLabel="✂️ Generate Clips"
          busyLabel="Clipping..."
          onAction={handleClips}
          disabled={busy || !hasPhrases || hasClips}
          note={
            hasClips
              ? 'Clips already generated. Use 🎵 Edit Clip on a card to adjust one.'
              : !hasPhrases
              ? 'Finish Step 1 first.'
              : undefined
          }
        />

        <StepCard
          number={3}
          title="Export to Anki"
          description="Download the .apkg deck with embedded audio + source link."
          state={step3}
          color="green"
          actionLabel="📦 Export to Anki"
          href={getExportUrl(job.id)}
          disabled={!hasClips || busy}
          note={!hasClips ? 'Finish Step 2 first.' : undefined}
        />
      </div>

      {/* ── Phrases ────────────────────────────────────────────── */}
      {loading ? (
        <p className="text-gray-500">Loading phrases...</p>
      ) : phrases.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <p className="text-gray-500">No phrases yet.</p>
          <p className="text-sm text-gray-400 mt-1">Run Step 1 to analyze the transcript.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {phrases.map((phrase) => (
            <PhraseCard
              key={phrase.id}
              phrase={phrase}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}