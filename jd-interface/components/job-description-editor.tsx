"use client";

import { useAtom, useSetAtom } from "jotai";
import { useState, useEffect, useRef } from "react";
import { jobDescriptionAtom, updateJDAtom } from "@/stores/jd-atoms";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { 
  FileText, 
  Building2, 
  MapPin, 
  DollarSign, 
  Clock, 
  CheckCircle, 
  Gift,
  Save,
  Download,
  Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";

export function JobDescriptionEditor() {
  const [jobDescription] = useAtom(jobDescriptionAtom);
  const updateJD = useSetAtom(updateJDAtom);
  
  // Track recently updated fields for visual feedback
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set());
  const [isAIExtracting, setIsAIExtracting] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(0);
  const prevJobDescription = useRef(jobDescription);
  const fieldRefs = useRef<Record<string, HTMLDivElement | null>>({});
  
  // Detect when fields are updated (likely by AI)
  useEffect(() => {
    const updatedFields = new Set<string>();
    
    // Compare current with previous to find changed fields
    Object.keys(jobDescription).forEach((key) => {
      const current = jobDescription[key as keyof typeof jobDescription];
      const previous = prevJobDescription.current[key as keyof typeof jobDescription];
      
      // Check for actual meaningful changes
      if (JSON.stringify(current) !== JSON.stringify(previous)) {
        // Only highlight if the field gained meaningful content (not just empty to empty)
        const currentHasContent = (typeof current === 'string' && current.trim()) || 
                                (Array.isArray(current) && current.length > 0);
        const previousHasContent = (typeof previous === 'string' && previous.trim()) || 
                                 (Array.isArray(previous) && previous.length > 0);
        
        // Only animate if we're gaining content or changing existing content
        if (currentHasContent && (!previousHasContent || current !== previous)) {
          updatedFields.add(key);
        }
      }
    });
    
    // Only trigger animation if we have genuinely new content
    if (updatedFields.size > 0) {
      console.log('✨ NEW content detected in fields:', Array.from(updatedFields));
      setRecentlyUpdated(updatedFields);
      setIsAIExtracting(true);
      setLastUpdateTime(Date.now());
      
      // Scroll to the first updated field for better UX
      const firstUpdatedField = Array.from(updatedFields)[0];
      if (firstUpdatedField && fieldRefs.current[firstUpdatedField]) {
        setTimeout(() => {
          fieldRefs.current[firstUpdatedField]?.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          });
        }, 200); // Small delay to allow DOM to update
      }
      
      // Clear the highlight after 3 seconds
      setTimeout(() => {
        setRecentlyUpdated(new Set());
        setIsAIExtracting(false);
      }, 3000);
    }
    
    prevJobDescription.current = jobDescription;
  }, [jobDescription]);

  const handleInputChange = (field: keyof typeof jobDescription, value: string | string[]) => {
    updateJD({ [field]: value });
  };

  const handleRequirementsChange = (value: string) => {
    const requirements = value
      .split('\n')
      .filter(req => req.trim() !== '')
      .map(req => req.trim());
    handleInputChange('requirements', requirements);
  };

  const handleBenefitsChange = (value: string) => {
    const benefits = value
      .split('\n')
      .filter(benefit => benefit.trim() !== '')
      .map(benefit => benefit.trim());
    handleInputChange('benefits', benefits);
  };

  const handleTechnicalSkillsChange = (value: string) => {
    const skills = value
      .split('\n')
      .filter(skill => skill.trim() !== '')
      .map(skill => skill.trim());
    handleInputChange('technicalSkills', skills);
  };

  const getCompletionStats = () => {
    const fields = [
      jobDescription.title,
      jobDescription.company,
      jobDescription.description,
      jobDescription.location,
      jobDescription.workArrangement,
      jobDescription.salaryRange,
      jobDescription.employmentType,
      jobDescription.experienceLevel,
      jobDescription.department,
      jobDescription.teamSize,
      jobDescription.educationRequirements,
      jobDescription.growthOpportunities,
    ];
    const arrayFields = [
      jobDescription.requirements,
      jobDescription.benefits,
      jobDescription.technicalSkills,
    ];
    
    const filledFields = fields.filter(Boolean).length;
    const filledArrays = arrayFields.filter(arr => arr.length > 0).length;
    const total = fields.length + arrayFields.length;
    const completed = filledFields + filledArrays;
    
    return {
      completed,
      total,
      percentage: Math.round((completed / total) * 100)
    };
  };

  const stats = getCompletionStats();
  
  // Helper function to check if a field was recently updated
  const isFieldRecentlyUpdated = (fieldName: string) => {
    return recentlyUpdated.has(fieldName);
  };
  
  // Helper function to get professional field styling
  const getFieldStyling = (fieldName: string) => {
    if (isFieldRecentlyUpdated(fieldName)) {
      return "animate-pulse ring-2 ring-green-400 ring-opacity-50 bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-600 transition-all duration-500";
    }
    return "transition-all duration-200 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400";
  };
  
  // Helper function to render professional field with AI indicator
  const renderFieldWithAI = (fieldName: string, children: React.ReactNode) => {
    const isUpdated = isFieldRecentlyUpdated(fieldName);
    return (
      <div 
        ref={(el) => {
          fieldRefs.current[fieldName] = el;
        }}
        className="relative group"
      >
        {children}
        {isUpdated && (
          <div className="absolute -top-3 -right-3 flex items-center gap-2 animate-in fade-in slide-in-from-right-2 duration-300">
            <div className="flex items-center gap-1 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium shadow-lg">
              <Sparkles className="w-3 h-3 animate-pulse" />
              LIVE
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full max-h-[calc(100vh-10rem)] overflow-y-auto flex flex-col ">
      {/* Header */}
      <div className="p-6 pb-4 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-50">Job Description Editor</h2>
              <div className="flex items-center gap-3">
                {isAIExtracting && (
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-xs font-medium">AI Updating</span>
                  </div>
                )}
                {!isAIExtracting && lastUpdateTime > 0 && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Updated {Math.floor((Date.now() - lastUpdateTime) / 1000)}s ago
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isAIExtracting && (
              <div className="px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-medium flex items-center gap-2 animate-pulse">
                <Sparkles className="w-3 h-3" />
                Live AI
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs font-medium">
                {stats.completed}/{stats.total}
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                stats.percentage === 100 
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' 
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              }`}>
                {stats.percentage}% Complete
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content - Vertical Layout */}
      <div className="flex-1 overflow-y-auto p-6 bg-white dark:bg-slate-800 space-y-8">
        
        {/* Basic Information Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h3>
          </div>
          <div className="grid gap-6">
            {renderFieldWithAI('title', 
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-blue-500 rounded-full"></div>
                  Job Title
                </label>
                <Input
                  placeholder="e.g. Senior React Developer"
                  value={jobDescription.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('title'))}
                />
              </div>
            )}
            
            {renderFieldWithAI('company',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-purple-500 rounded-full"></div>
                  Company
                </label>
                <Input
                  placeholder="e.g. Tech Innovations Inc."
                  value={jobDescription.company}
                  onChange={(e) => handleInputChange('company', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('company'))}
                />
              </div>
            )}
            
            {renderFieldWithAI('description',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-green-500 rounded-full"></div>
                  Job Description
                </label>
                <Textarea
                  placeholder="Describe the role, responsibilities, and what makes this position exciting..."
                  value={jobDescription.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className={cn("min-h-36 text-base leading-relaxed resize-none", getFieldStyling('description'))}
                />
              </div>
            )}
          </div>
        </section>

        {/* Requirements Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Requirements</h3>
          </div>
          {renderFieldWithAI('requirements',
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-orange-500 rounded-full"></div>
                  Requirements
                </label>
                <div className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs font-medium text-gray-600 dark:text-gray-400">
                  {jobDescription.requirements.length} item{jobDescription.requirements.length !== 1 ? 's' : ''}
                </div>
              </div>
              <Textarea
                placeholder="• 5+ years experience with React
• Strong knowledge of TypeScript
• Experience with Next.js
• Understanding of modern web technologies"
                value={jobDescription.requirements.join('\n')}
                onChange={(e) => handleRequirementsChange(e.target.value)}
                className={cn("min-h-40 text-base leading-relaxed resize-none", getFieldStyling('requirements'))}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                Enter each requirement on a new line
              </p>
            </div>
          )}
        </section>

        {/* Benefits Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <Gift className="w-5 h-5 text-pink-600 dark:text-pink-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Benefits & Perks</h3>
          </div>
          {renderFieldWithAI('benefits',
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-pink-500 rounded-full"></div>
                  Benefits & Perks
                </label>
                <div className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs font-medium text-gray-600 dark:text-gray-400">
                  {jobDescription.benefits.length} benefit{jobDescription.benefits.length !== 1 ? 's' : ''}
                </div>
              </div>
              <Textarea
                placeholder="• Comprehensive health, dental, and vision insurance
• Flexible work schedule and remote options
• Professional development budget
• Generous PTO and parental leave"
                value={jobDescription.benefits.join('\n')}
                onChange={(e) => handleBenefitsChange(e.target.value)}
                className={cn("min-h-40 text-base leading-relaxed resize-none", getFieldStyling('benefits'))}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                List each benefit on a new line
              </p>
            </div>
          )}
        </section>

        {/* Job Details Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-teal-600 dark:text-teal-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Job Details</h3>
          </div>
          <div className="grid gap-6">
            {renderFieldWithAI('location',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  Location
                </label>
                <Input
                  placeholder="e.g. San Francisco, CA (Remote friendly)"
                  value={jobDescription.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('location'))}
                />
              </div>
            )}
            
            {renderFieldWithAI('salaryRange',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-gray-500" />
                  Salary Range
                </label>
                <Input
                  placeholder="e.g. $120,000 - $150,000"
                  value={jobDescription.salaryRange}
                  onChange={(e) => handleInputChange('salaryRange', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('salaryRange'))}
                />
              </div>
            )}
            
            {renderFieldWithAI('employmentType',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  Employment Type
                </label>
                <Input
                  placeholder="e.g. Full-time, Part-time, Contract"
                  value={jobDescription.employmentType}
                  onChange={(e) => handleInputChange('employmentType', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('employmentType'))}
                />
              </div>
            )}

            {renderFieldWithAI('workArrangement',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  Work Arrangement
                </label>
                <Input
                  placeholder="e.g. Remote, Hybrid, Onsite"
                  value={jobDescription.workArrangement}
                  onChange={(e) => handleInputChange('workArrangement', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('workArrangement'))}
                />
              </div>
            )}

            {renderFieldWithAI('experienceLevel',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-gray-500" />
                  Experience Level
                </label>
                <Input
                  placeholder="e.g. Junior, Mid-level, Senior"
                  value={jobDescription.experienceLevel}
                  onChange={(e) => handleInputChange('experienceLevel', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('experienceLevel'))}
                />
              </div>
            )}

            {renderFieldWithAI('department',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-gray-500" />
                  Department
                </label>
                <Input
                  placeholder="e.g. Engineering, Marketing, Sales"
                  value={jobDescription.department}
                  onChange={(e) => handleInputChange('department', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('department'))}
                />
              </div>
            )}

            {renderFieldWithAI('teamSize',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-gray-500" />
                  Team Size
                </label>
                <Input
                  placeholder="e.g. 5-10 people, Small team, Large team"
                  value={jobDescription.teamSize}
                  onChange={(e) => handleInputChange('teamSize', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('teamSize'))}
                />
              </div>
            )}

            {renderFieldWithAI('educationRequirements',
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-500" />
                  Education Requirements
                </label>
                <Input
                  placeholder="e.g. Bachelor's degree in CS, No degree required"
                  value={jobDescription.educationRequirements}
                  onChange={(e) => handleInputChange('educationRequirements', e.target.value)}
                  className={cn("h-11 text-base", getFieldStyling('educationRequirements'))}
                />
              </div>
            )}
          </div>
        </section>

        {/* Technical Skills Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Technical Skills</h3>
          </div>
          {renderFieldWithAI('technicalSkills',
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                  <div className="w-1 h-4 bg-indigo-500 rounded-full"></div>
                  Technical Skills
                </label>
                <div className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs font-medium text-gray-600 dark:text-gray-400">
                  {jobDescription.technicalSkills.length} skill{jobDescription.technicalSkills.length !== 1 ? 's' : ''}
                </div>
              </div>
              <Textarea
                placeholder="• Python
• React
• Node.js
• PostgreSQL
• Docker"
                value={jobDescription.technicalSkills.join('\n')}
                onChange={(e) => handleTechnicalSkillsChange(e.target.value)}
                className={cn("min-h-32 text-base leading-relaxed resize-none", getFieldStyling('technicalSkills'))}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                Enter each skill on a new line
              </p>
            </div>
          )}
        </section>

        {/* Growth Opportunities Section */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Growth & Development</h3>
          </div>
          {renderFieldWithAI('growthOpportunities',
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
                <div className="w-1 h-4 bg-purple-500 rounded-full"></div>
                Growth Opportunities
              </label>
              <Textarea
                placeholder="Describe career growth opportunities, learning paths, mentorship programs, advancement possibilities..."
                value={jobDescription.growthOpportunities}
                onChange={(e) => handleInputChange('growthOpportunities', e.target.value)}
                className={cn("min-h-28 text-base leading-relaxed resize-none", getFieldStyling('growthOpportunities'))}
              />
            </div>
          )}
        </section>

        {/* Action Buttons */}
        <section className="border-t border-gray-200 dark:border-slate-700 pt-6">
          <div className="flex gap-3">
            <Button variant="outline" className="flex-1 h-11 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200">
              <Save className="w-4 h-4 mr-2" />
              Save Draft
            </Button>
            <Button className="flex-1 h-11 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400 text-white">
              <Download className="w-4 h-4 mr-2" />
              Export Job Description
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default JobDescriptionEditor;