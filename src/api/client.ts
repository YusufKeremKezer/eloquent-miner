import type { Job, Phrase } from '../types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Request failed');
  }

  return res.json();
}

// Jobs
export const getJobs = () => request<Job[]>('/jobs');

export const getJob = (id: string) => request<Job>(`/jobs/${id}`);

export const createJob = (data: { source_type: string; title?: string; language?: string }) =>
  request<Job>('/jobs', { method: 'POST', body: JSON.stringify(data) });

export const deleteJob = (id: string) =>
  request<void>(`/jobs/${id}`, { method: 'DELETE' });

// YouTube
export const processYouTube = (url: string, title?: string) =>
  request<any>('/youtube/process', {
    method: 'POST',
    body: JSON.stringify({ url, title }),
  });

// Extraction
export const extractPhrases = (jobId: string) =>
  request<Phrase[]>(`/jobs/${jobId}/extract`, { method: 'POST' });

// Phrases
export const getPhrases = (jobId: string) =>
  request<Phrase[]>(`/jobs/${jobId}/phrases`);

export const approvePhrase = (phraseId: number) =>
  request<Phrase>(`/phrases/${phraseId}/approve`, { method: 'POST' });

export const rejectPhrase = (phraseId: number) =>
  request<Phrase>(`/phrases/${phraseId}/reject`, { method: 'POST' });

// Clips
export const generateClips = (jobId: string) =>
  request<Phrase[]>(`/jobs/${jobId}/clips`, { method: 'POST' });

// Export
export const getExportUrl = (jobId: string) =>
  `${BASE}/jobs/${jobId}/export/anki`;

// Media
export const getMediaUrl = (filename: string) =>
  `/media/${filename}`;