import { useState, type SyntheticEvent } from 'react';
import type { Phrase } from '../types';
import { updatePhrase, deletePhrase, reclipPhrase } from '../api/client';
import AudioPlayer from './AudioPlayer';

interface Props {
  phrase: Phrase;
  onUpdate: (phrase: Phrase) => void;
  onDelete: (phrase: Phrase) => void;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
}

function PreviewPlayer({ jobId, startTime, endTime }: {
  jobId: string;
  startTime: number;
  endTime: number;
}) {
  const audioId = `preview-${jobId}-${startTime}-${endTime}`;

  const handlePlay = () => {
    const audio = document.getElementById(audioId) as HTMLAudioElement;
    if (audio) {
      audio.currentTime = startTime;
      audio.play();
    }
  };

  const handleTimeUpdate = (e: SyntheticEvent<HTMLAudioElement>) => {
    const audio = e.currentTarget;
    if (audio.currentTime >= endTime) {
      audio.pause();
      audio.currentTime = startTime;
    }
  };

  return (
    <div className="flex items-center gap-2">
      <audio
        id={audioId}
        controls
        className="flex-1 h-8"
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
      >
        <source src={`/media/${jobId}/source.mp3?v=${Date.now()}`} type="audio/mpeg" />
      </audio>
      <button
        onClick={handlePlay}
        className="px-3 py-1.5 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 whitespace-nowrap"
      >
        ▶ {formatTime(startTime)}–{formatTime(endTime)}
      </button>
    </div>
  );
}

export default function PhraseCard({ phrase, onUpdate, onDelete }: Props) {
  const [editingText, setEditingText] = useState(false);
  const [editingAudio, setEditingAudio] = useState(false);

  const [editPhrase, setEditPhrase] = useState(phrase.phrase);
  const [editDefinition, setEditDefinition] = useState(phrase.definition || '');
  const [editUsage, setEditUsage] = useState(phrase.usage || '');
  const [editExampleNew, setEditExampleNew] = useState(phrase.example_new || '');

  const [clipStart, setClipStart] = useState(phrase.start || 0);
  const [clipEnd, setClipEnd] = useState(phrase.end || 0);
  const [reclipping, setReclipping] = useState(false);
  const [saving, setSaving] = useState(false);

  const clipDuration = clipEnd - clipStart;

  const handleSaveText = async () => {
    setSaving(true);
    try {
      const updated = await updatePhrase(phrase.id, {
        phrase: editPhrase,
        definition: editDefinition,
        usage: editUsage,
        example_new: editExampleNew,
      });
      setEditingText(false);
      onUpdate(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleReclip = async () => {
    if (clipStart < 0) return alert('Start time cannot be negative');
    if (clipEnd <= clipStart) return alert('End must be after start');
    if (clipEnd - clipStart > 60) return alert('Clip cannot be longer than 60 seconds');
    if (clipEnd - clipStart < 0.5) return alert('Clip must be at least 0.5 seconds');

    setReclipping(true);
    try {
      const updated = await reclipPhrase(phrase.id, clipStart, clipEnd);
      setEditingAudio(false);
      onUpdate(updated);
    } catch (err: any) {
      alert(`Reclip failed: ${err.message}`);
    } finally {
      setReclipping(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this phrase? It will not be exported to Anki.')) return;
    await deletePhrase(phrase.id);
    onDelete(phrase);
  };

  const expandClip = (seconds: number) => {
    const center = (clipStart + clipEnd) / 2;
    setClipStart(Math.round(Math.max(0, center - seconds / 2) * 10) / 10);
    setClipEnd(Math.round((center + seconds / 2) * 10) / 10);
  };

  const extendBefore = (seconds: number) => {
    setClipStart(Math.max(0, Math.round((clipStart - seconds) * 10) / 10));
  };

  const extendAfter = (seconds: number) => {
    setClipEnd(Math.round((clipEnd + seconds) * 10) / 10);
  };

  // ─── Audio Edit Mode ───────────────────────────────────────────
  if (editingAudio) {
    return (
      <div className="border border-purple-300 rounded-xl p-4 bg-purple-50">
        <h3 className="text-sm font-semibold text-purple-700 mb-3">🎵 Audio Clip Editor</h3>

        <div className="text-sm text-gray-600 mb-2 font-medium">"{phrase.phrase}"</div>

        <div className="flex gap-4 text-xs text-gray-500 mb-3">
          <span>Start: {formatTime(clipStart)}</span>
          <span>End: {formatTime(clipEnd)}</span>
          <span>Duration: {clipDuration.toFixed(1)}s</span>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <button onClick={() => expandClip(10)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">📏 Make 10s</button>
          <button onClick={() => expandClip(15)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">📏 Make 15s</button>
          <button onClick={() => extendBefore(2)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">⏪ Start −2s</button>
          <button onClick={() => extendAfter(2)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">End +2s ⏩</button>
          <button onClick={() => extendBefore(-1)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">⏩ Trim start +1s</button>
          <button onClick={() => extendAfter(-1)} className="px-3 py-1.5 bg-purple-100 text-purple-700 text-xs rounded-lg hover:bg-purple-200">⏪ Trim end −1s</button>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Start (seconds)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={clipStart}
              onChange={(e) => setClipStart(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">End (seconds)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={clipEnd}
              onChange={(e) => setClipEnd(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Start: {formatTime(clipStart)}</label>
            <input
              type="range"
              min="0"
              max={Math.max(clipEnd, 300)}
              step="0.1"
              value={clipStart}
              onChange={(e) => setClipStart(parseFloat(e.target.value))}
              className="w-full accent-purple-600"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">End: {formatTime(clipEnd)}</label>
            <input
              type="range"
              min={clipStart}
              max={Math.max(clipEnd + 30, 300)}
              step="0.1"
              value={clipEnd}
              onChange={(e) => setClipEnd(parseFloat(e.target.value))}
              className="w-full accent-purple-600"
            />
          </div>
        </div>

        <div className="p-3 bg-white rounded-lg border border-purple-200 mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">🎧 Preview selected range from source audio:</div>
          <PreviewPlayer jobId={phrase.job_id} startTime={clipStart} endTime={clipEnd} />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleReclip}
            disabled={reclipping || clipEnd <= clipStart}
            className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {reclipping ? '✂️ Cutting...' : '✂️ Re-cut Clip'}
          </button>
          <button
            onClick={() => setEditingAudio(false)}
            className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>

        {clipEnd <= clipStart && <p className="mt-2 text-xs text-red-600">End must be after start</p>}
      </div>
    );
  }

  // ─── Text Edit Mode ────────────────────────────────────────────
  if (editingText) {
    return (
      <div className="border border-blue-300 rounded-xl p-4 bg-blue-50">
        <h3 className="text-sm font-semibold text-blue-700 mb-3">✏️ Editing Text</h3>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Phrase</label>
            <input type="text" value={editPhrase} onChange={(e) => setEditPhrase(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Definition</label>
            <textarea value={editDefinition} onChange={(e) => setEditDefinition(e.target.value)} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Usage</label>
            <textarea value={editUsage} onChange={(e) => setEditUsage(e.target.value)} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">New Example</label>
            <textarea value={editExampleNew} onChange={(e) => setEditExampleNew(e.target.value)} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <button onClick={handleSaveText} disabled={saving} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Saving...' : '💾 Save'}
          </button>
          <button onClick={() => setEditingText(false)} className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  }

  // ─── Normal View ───────────────────────────────────────────────
  return (
    <div className="border border-gray-200 bg-white rounded-xl p-4">
      <h3 className="text-lg font-semibold text-gray-900">"{phrase.phrase}"</h3>

      {phrase.start !== null && phrase.end !== null && (
        <div className="mt-1 text-xs text-gray-400">
          🎵 {formatTime(phrase.start)} → {formatTime(phrase.end)} ({(phrase.end - phrase.start).toFixed(1)}s)
        </div>
      )}

      {phrase.definition && <p className="mt-2 text-sm text-gray-600">{phrase.definition}</p>}
      {phrase.usage && <p className="mt-1 text-sm text-gray-500 italic">{phrase.usage}</p>}

      <div className="mt-3 space-y-1">
        {phrase.example_original && (
          <p className="text-sm"><span className="font-medium text-gray-700">Original:</span> <span className="text-gray-600">{phrase.example_original}</span></p>
        )}
        {phrase.example_new && (
          <p className="text-sm"><span className="font-medium text-gray-700">New:</span> <span className="text-gray-600">{phrase.example_new}</span></p>
        )}
      </div>

      {phrase.alternatives && phrase.alternatives.length > 0 && (
        <div className="mt-2">
          <span className="text-xs font-medium text-gray-500">Alternatives:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {phrase.alternatives.map((alt, i) => (
              <span key={i} className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">{alt}</span>
            ))}
          </div>
        </div>
      )}

      {phrase.register && <div className="mt-2 text-xs text-gray-500">Register: {phrase.register}</div>}
      {phrase.why_eloquent && <p className="mt-1 text-xs text-gray-400 italic">{phrase.why_eloquent}</p>}

      {phrase.audio_filename && (
        <div className="mt-3">
          <AudioPlayer filename={phrase.audio_filename} />
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {phrase.audio_filename && (
          <button
            onClick={() => {
              setClipStart(phrase.start || 0);
              setClipEnd(phrase.end || 0);
              setEditingAudio(true);
            }}
            className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700"
          >
            🎵 Edit Clip
          </button>
        )}
        <button onClick={() => setEditingText(true)} className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">✏️ Edit Text</button>
        <button onClick={handleDelete} className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">🗑️ Delete</button>
      </div>
    </div>
  );
}