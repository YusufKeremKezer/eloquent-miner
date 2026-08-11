import { useEffect, useState } from 'react';
import type { Job, Phrase } from '../types';
import {
  getPhrases,
  extractPhrases,
  generateClips,
  approvePhrase,
  rejectPhrase,
  getExportUrl,
} from '../api/client';
import PhraseCard from '../components/PhraseCard';

interface Props {
  job: Job;
  onBack: () => void;
}

export default function JobDetailPage({ job, onBack }: Props) {
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [clipping, setClipping] = useState(false);

  const fetchPhrases = async () => {
    setLoading(true);
    try {
      const data = await getPhrases(job.id);
      setPhrases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhrases();
  }, [job.id]);

  const handleExtract = async () => {
    setExtracting(true);
    try {
      await extractPhrases(job.id);
      await fetchPhrases();
      alert('Extraction complete!');
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleClips = async () => {
    setClipping(true);
    try {
      await generateClips(job.id);
      await fetchPhrases();
      alert('Clips generated!');
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setClipping(false);
    }
  };

  const handleApprove = async (phrase: Phrase) => {
    await approvePhrase(phrase.id);
    fetchPhrases();
  };

  const handleReject = async (phrase: Phrase) => {
    await rejectPhrase(phrase.id);
    fetchPhrases();
  };

  const approvedCount = phrases.filter(p => p.status === 'approved').length;
  const rejectedCount = phrases.filter(p => p.status === 'rejected').length;
  const candidateCount = phrases.filter(p => p.status === 'candidate').length;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <button
        onClick={onBack}
        className="text-blue-600 hover:text-blue-800 mb-4 inline-block"
      >
        ← Back to Jobs
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {job.title || 'Untitled Job'}
        </h1>
        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
            {job.status}
          </span>
          <span>{phrases.length} phrases</span>
          <span className="text-green-600">{approvedCount} approved</span>
          <span className="text-red-600">{rejectedCount} rejected</span>
          <span className="text-yellow-600">{candidateCount} pending</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3 mb-6">
        <button
          onClick={handleExtract}
          disabled={extracting}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {extracting ? 'Extracting...' : '🧠 Extract Phrases'}
        </button>

        <button
          onClick={handleClips}
          disabled={clipping}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {clipping ? 'Clipping...' : '✂️ Generate Clips'}
        </button>

        <a
          href={getExportUrl(job.id)}
          download
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          📦 Export to Anki
        </a>
      </div>

      {/* Phrases */}
      {loading ? (
        <p className="text-gray-500">Loading phrases...</p>
      ) : phrases.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <p className="text-gray-500">No phrases yet.</p>
          <p className="text-sm text-gray-400 mt-1">
            Click "Extract Phrases" to analyze the transcript.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {phrases.map((phrase) => (
            <PhraseCard
              key={phrase.id}
              phrase={phrase}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>
      )}
    </div>
  );
}