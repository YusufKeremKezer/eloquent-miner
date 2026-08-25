import { useEffect, useState } from 'react';
import type { Job } from '../types';
import { getJobs, deleteJob } from '../api/client';
import JobCard from '../components/JobCard';
import NewJobForm from '../components/NewJobForm';

interface Props {
  onSelectJob: (job: Job) => void;
}

export default function HomePage({ onSelectJob }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await getJobs();
      setJobs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDelete = async (job: Job) => {
    if (!confirm(`Delete job "${job.title}"?`)) return;
    await deleteJob(job.id);
    fetchJobs();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Eloquent Miner</h1>
        <p className="text-gray-500 mt-1">
          Extract eloquent English phrases from videos and create Anki flashcards.
        </p>
      </header>

      <NewJobForm onCreated={fetchJobs} />

      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Jobs</h2>

        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : jobs.length === 0 ? (
          <p className="text-gray-500">No jobs yet. Create one above!</p>
        ) : (
          <div className="grid gap-3">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onSelect={onSelectJob}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}