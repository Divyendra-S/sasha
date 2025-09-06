import { atom } from 'jotai';

export interface JobDescription {
  title: string;
  company: string;
  description: string;
  requirements: string[];
  benefits: string[];
  location: string;
  salaryRange: string;
  employmentType: string;
}

export interface VoiceSession {
  isConnected: boolean;
  isListening: boolean;
  transcript: string[];
  lastMessage: string;
  isProcessing: boolean;
  lastUpdate: number;
}

// Core atoms
export const jobDescriptionAtom = atom<JobDescription>({
  title: '',
  company: '',
  description: '',
  requirements: [],
  benefits: [],
  location: '',
  salaryRange: '',
  employmentType: 'Full-time',
});

export const voiceSessionAtom = atom<VoiceSession>({
  isConnected: false,
  isListening: false,
  transcript: [],
  lastMessage: '',
  isProcessing: false,
  lastUpdate: 0,
});

// Action atoms
export const updateJDAtom = atom(
  null,
  (get, set, updates: Partial<JobDescription>) => {
    const current = get(jobDescriptionAtom);
    set(jobDescriptionAtom, { ...current, ...updates });
  }
);

export const addVoiceMessageAtom = atom(
  null,
  (get, set, message: string) => {
    const current = get(voiceSessionAtom);
    set(voiceSessionAtom, {
      ...current,
      transcript: [...current.transcript, message],
      lastMessage: message,
      lastUpdate: Date.now(),
    });
  }
);

export const updateVoiceStatusAtom = atom(
  null,
  (get, set, status: Partial<VoiceSession>) => {
    const current = get(voiceSessionAtom);
    set(voiceSessionAtom, { ...current, ...status, lastUpdate: Date.now() });
  }
);