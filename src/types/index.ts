export interface Job {
    id: string;
    status: string;
    source_type: string;
    source_url: string | null;
    title: string | null;
    language: string;
    created_at: string;
  }
  
  export interface Phrase {
    id: number;
    job_id: string;
    phrase: string;
    start: number | null;
    end: number | null;
    definition: string | null;
    usage: string | null;
    example_original: string | null;
    example_new: string | null;
    register: string | null;
    alternatives: string[];
    why_eloquent: string | null;
    status: string;
    audio_filename: string | null;
    created_at: string;
  }
  
  export interface Segment {
    id: number;
    job_id: string;
    start: number | null;
    end: number | null;
    text: string;
  }