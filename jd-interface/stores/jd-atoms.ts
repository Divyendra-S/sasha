import { atom } from 'jotai';

export interface JobDescription {
  title: string;
  company: string;
  description: string;
  requirements: string[];
  benefits: string[];
  location: string;
  workArrangement: string;
  salaryRange: string;
  employmentType: string;
  experienceLevel: string;
  department: string;
  teamSize: string;
  technicalSkills: string[];
  educationRequirements: string;
  growthOpportunities: string;
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
  workArrangement: '',
  salaryRange: '',
  employmentType: 'Full-time',
  experienceLevel: '',
  department: '',
  teamSize: '',
  technicalSkills: [],
  educationRequirements: '',
  growthOpportunities: '',
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
    const newState = { ...current, ...updates };
    
    // Log the update for debugging
    console.log('🔄 JD Data Updated:', {
      previous: current,
      updates,
      new: newState
    });
    
    set(jobDescriptionAtom, newState);
  }
);

// Bulk update with field validation
export const bulkUpdateJDAtom = atom(
  null,
  (get, set, data: any) => {
    if (!data || typeof data !== 'object') {
      console.warn('⚠️ Invalid JD data provided:', data);
      return;
    }
    
    console.log('📊 Bulk update received:', data);
    console.log('📊 Data keys:', Object.keys(data));
    
    const current = get(jobDescriptionAtom);
    const validUpdates: Partial<JobDescription> = {};
    
    // Map and validate fields - backend field names to frontend field names
    const fieldMapping: Record<string, keyof JobDescription> = {
      title: 'title',
      job_title: 'title',
      company: 'company', 
      company_name: 'company',
      description: 'description',
      responsibilities: 'description',
      requirements: 'requirements',
      required_qualifications: 'requirements',
      benefits: 'benefits',
      preferred_qualifications: 'benefits',
      location: 'location',
      work_arrangement: 'workArrangement',
      salaryRange: 'salaryRange',
      salary_range: 'salaryRange',
      employmentType: 'employmentType',
      employment_type: 'employmentType',
      experience_level: 'experienceLevel',
      department: 'department',
      team_size: 'teamSize',
      technical_skills: 'technicalSkills',
      education_requirements: 'educationRequirements',
      growth_opportunities: 'growthOpportunities'
    };
    
    for (const [sourceField, targetField] of Object.entries(fieldMapping)) {
      if (sourceField in data && data[sourceField] !== undefined) {
        const value = data[sourceField];
        
        // Validate array fields
        if ((targetField === 'requirements' || targetField === 'benefits' || targetField === 'technicalSkills') && Array.isArray(value)) {
          (validUpdates as any)[targetField] = value.filter(item => item && typeof item === 'string');
        }
        // Convert string to array for technical_skills if needed
        else if (targetField === 'technicalSkills' && typeof value === 'string') {
          (validUpdates as any)[targetField] = [value];
        }
        // Convert array to string for requirements/benefits if needed (for backend compatibility)  
        else if ((targetField === 'requirements' || targetField === 'benefits') && typeof value === 'string') {
          (validUpdates as any)[targetField] = value.split('\n').filter(item => item.trim());
        }
        // Validate string fields
        else if (typeof value === 'string') {
          (validUpdates as any)[targetField] = value;
        }
        // Log invalid types
        else {
          console.warn(`⚠️ Invalid type for ${targetField}:`, typeof value, value);
        }
      }
    }
    
    if (Object.keys(validUpdates).length > 0) {
      const newState = { ...current, ...validUpdates };
      
      console.log('✅ Bulk JD Update Applied:', {
        fieldsUpdated: Object.keys(validUpdates),
        validUpdates,
        previousState: current,
        newState
      });
      
      set(jobDescriptionAtom, newState);
    } else {
      console.warn('⚠️ No valid fields to update in bulk update');
      console.log('📊 Raw data received:', data);
      console.log('📊 Field mapping results:', Object.entries(fieldMapping).map(([source, target]) => ({
        source,
        target, 
        hasData: source in data,
        value: data[source],
        type: typeof data[source]
      })));
    }
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