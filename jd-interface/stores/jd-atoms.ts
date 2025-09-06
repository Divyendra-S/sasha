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
      // Frontend field names (direct mapping)
      title: 'title',
      company: 'company',
      description: 'description',
      requirements: 'requirements',
      benefits: 'benefits',
      location: 'location',
      workArrangement: 'workArrangement',
      salaryRange: 'salaryRange',
      employmentType: 'employmentType',
      experienceLevel: 'experienceLevel',
      department: 'department',
      teamSize: 'teamSize',
      technicalSkills: 'technicalSkills',
      educationRequirements: 'educationRequirements',
      growthOpportunities: 'growthOpportunities',
      
      // Backend field names (snake_case to camelCase mapping)
      job_title: 'title',
      company_name: 'company',
      responsibilities: 'description',
      required_qualifications: 'requirements',
      preferred_qualifications: 'benefits',
      work_arrangement: 'workArrangement',
      salary_range: 'salaryRange',
      employment_type: 'employmentType',
      experience_level: 'experienceLevel',
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
        // Convert string to array for requirements/benefits if needed (for backend compatibility)  
        else if ((targetField === 'requirements' || targetField === 'benefits') && typeof value === 'string') {
          // Split by newlines first, then by common separators if no newlines
          let items = value.split('\n').filter(item => item.trim());
          if (items.length === 1 && items[0]) {
            // If no newlines, try splitting by commas, semicolons, or bullet points
            items = items[0].split(/[,;•]/).map(item => item.trim()).filter(item => item);
          }
          (validUpdates as any)[targetField] = items;
        }
        // Convert number to string for teamSize field
        else if (targetField === 'teamSize' && typeof value === 'number') {
          (validUpdates as any)[targetField] = value.toString();
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