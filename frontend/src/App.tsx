import { useState } from 'react';
import type { Job } from './types';
import HomePage from './pages/HomePage';
import JobDetailPage from './pages/JobDetailPage';

export default function App() {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  if (selectedJob) {
    return (
      <JobDetailPage
        job={selectedJob}
        onBack={() => setSelectedJob(null)}
      />
    );
  }

  return <HomePage onSelectJob={setSelectedJob} />;
}