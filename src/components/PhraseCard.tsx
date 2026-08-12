import type { Phrase } from '../types';
import AudioPlayer from './AudioPlayer';

interface Props {
  phrase: Phrase;
  onApprove: (phrase: Phrase) => void;
  onReject: (phrase: Phrase) => void;
}

export default function PhraseCard({ phrase, onApprove, onReject }: Props) {
  const statusStyles: Record<string, string> = {
    candidate: 'border-yellow-200 bg-yellow-50',
    approved: 'border-green-200 bg-green-50',
    rejected: 'border-red-200 bg-red-50',
  };

  return (
    <div className={`border rounded-xl p-4 ${statusStyles[phrase.status] || 'border-gray-200 bg-white'}`}>
      {/* Phrase */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-lg font-semibold text-gray-900">
          "{phrase.phrase}"
        </h3>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          phrase.status === 'approved' ? 'bg-green-100 text-green-700' :
          phrase.status === 'rejected' ? 'bg-red-100 text-red-700' :
          'bg-yellow-100 text-yellow-700'
        }`}>
          {phrase.status}
        </span>
      </div>

      {/* Definition */}
      {phrase.definition && (
        <p className="mt-2 text-sm text-gray-600">{phrase.definition}</p>
      )}

      {/* Usage */}
      {phrase.usage && (
        <p className="mt-1 text-sm text-gray-500 italic">{phrase.usage}</p>
      )}

      {/* Examples */}
      <div className="mt-3 space-y-1">
        {phrase.example_original && (
          <p className="text-sm">
            <span className="font-medium text-gray-700">Original:</span>{' '}
            <span className="text-gray-600">{phrase.example_original}</span>
          </p>
        )}
        {phrase.example_new && (
          <p className="text-sm">
            <span className="font-medium text-gray-700">New:</span>{' '}
            <span className="text-gray-600">{phrase.example_new}</span>
          </p>
        )}
      </div>

      {/* Alternatives */}
      {phrase.alternatives && phrase.alternatives.length > 0 && (
        <div className="mt-2">
          <span className="text-xs font-medium text-gray-500">Alternatives:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {phrase.alternatives.map((alt, i) => (
              <span key={i} className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                {alt}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Register & Why */}
      <div className="mt-2 flex gap-4 text-xs text-gray-500">
        {phrase.register && <span>Register: {phrase.register}</span>}
      </div>

      {phrase.why_eloquent && (
        <p className="mt-1 text-xs text-gray-400 italic">{phrase.why_eloquent}</p>
      )}

      {/* Audio */}
      {phrase.audio_filename && (
        <div className="mt-3">
          <AudioPlayer filename={phrase.audio_filename} />
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        {phrase.status !== 'approved' && (
          <button
            onClick={() => onApprove(phrase)}
            className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
          >
            ✓ Approve
          </button>
        )}
        {phrase.status !== 'rejected' && (
          <button
            onClick={() => onReject(phrase)}
            className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
          >
            ✗ Reject
          </button>
        )}
      </div>
    </div>
  );
}