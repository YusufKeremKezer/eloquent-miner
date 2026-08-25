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

  // 204 No Content → boş body, JSON parse etme
  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
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

export const updatePhrase = (phraseId: number, data: Partial<Phrase>) =>
  request<Phrase>(`/phrases/${phraseId}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deletePhrase = (phraseId: number) =>
  request<void>(`/phrases/${phraseId}`, { method: 'DELETE' });
// Clips

export const generateClips = (jobId: string) =>
  request<Phrase[]>(`/jobs/${jobId}/clips`, { method: 'POST' });

export const reclipPhrase = (phraseId: number, start: number, end: number) =>
  request<Phrase>(`/phrases/${phraseId}/reclip`, {
    method: 'POST',
    body: JSON.stringify({ start, end }),
  });

// Export
export const getExportUrl = (jobId: string) =>
  `${BASE}/jobs/${jobId}/export/anki`;

// Media
export const getMediaUrl = (filename: string) =>
  `/media/${filename}`;