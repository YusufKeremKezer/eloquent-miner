import type { Job } from '../types';

interface Props {
  job: Job;
  onSelect: (job: Job) => void;
  onDelete: (job: Job) => void;
}

export default function JobCard({ job, onSelect, onDelete }: Props) {
  const statusColors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    transcript_ready: 'bg-blue-100 text-blue-700',
    extracting: 'bg-yellow-100 text-yellow-700',
    audio_ready: 'bg-purple-100 text-purple-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <div
      className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
      onClick={() => onSelect(job)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">
            {job.title || 'Untitled Job'}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {job.source_type} • {new Date(job.created_at).toLocaleDateString()}
          </p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[job.status] || 'bg-gray-100 text-gray-600'}`}>
          {job.status}
        </span>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(job);
          }}
          className="text-xs text-red-500 hover:text-red-700"
        >
          Delete
        </button>
      </div>
    </div>
  );
}