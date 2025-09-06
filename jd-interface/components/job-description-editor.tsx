"use client";

import { useAtom, useSetAtom } from "jotai";
import { useState, useEffect, useRef } from "react";
import { jobDescriptionAtom, updateJDAtom } from "@/stores/jd-atoms";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
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
  Sparkles,
  Zap
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

  const getCompletionStats = () => {
    const fields = [
      jobDescription.title,
      jobDescription.company,
      jobDescription.description,
      jobDescription.location,
      jobDescription.salaryRange,
      jobDescription.employmentType,
    ];
    const arrayFields = [
      jobDescription.requirements,
      jobDescription.benefits,
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
  
  // Helper function to get field styling
  const getFieldStyling = (fieldName: string) => {
    if (isFieldRecentlyUpdated(fieldName)) {
      return "animate-pulse ring-2 ring-green-500 ring-opacity-100 bg-green-50 border-green-400 transition-all duration-300";
    }
    return "transition-all duration-300";
  };
  
  // Helper function to render field icon with AI indicator
  const renderFieldWithAI = (fieldName: string, children: React.ReactNode) => {
    const isUpdated = isFieldRecentlyUpdated(fieldName);
    return (
      <div className="relative">
        {children}
        {isUpdated && (
          <div className="absolute -top-2 -right-2 flex items-center gap-1 animate-bounce">
            <Sparkles className="w-4 h-4 text-green-500 animate-spin" />
            <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full font-medium shadow-sm">
              LIVE
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            <CardTitle className="text-lg">Job Description</CardTitle>
            {isAIExtracting && (
              <div className="flex items-center gap-1 text-green-600">
                <Zap className="w-4 h-4 animate-pulse" />
                <span className="text-sm font-medium">Live Update!</span>
              </div>
            )}
            {!isAIExtracting && lastUpdateTime > 0 && (
              <div className="text-xs text-muted-foreground">
                Last updated {Math.floor((Date.now() - lastUpdateTime) / 1000)}s ago
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isAIExtracting && (
              <Badge variant="outline" className="animate-pulse border-green-400 text-green-700">
                <Sparkles className="w-3 h-3 mr-1" />
                AI Active
              </Badge>
            )}
            <Badge variant="outline">
              {stats.completed}/{stats.total} Complete
            </Badge>
            <Badge variant={stats.percentage === 100 ? "default" : "secondary"}>
              {stats.percentage}%
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden">
        <Tabs defaultValue="overview" className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center gap-1">
              <Building2 className="w-3 h-3" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="requirements" className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Requirements
            </TabsTrigger>
            <TabsTrigger value="benefits" className="flex items-center gap-1">
              <Gift className="w-3 h-3" />
              Benefits
            </TabsTrigger>
            <TabsTrigger value="details" className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              Details
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="flex-1 space-y-4">
            <div className="grid gap-4">
              {renderFieldWithAI('title', 
                <div>
                  <label className="text-sm font-medium mb-1 block">Job Title</label>
                  <Input
                    placeholder="e.g. Senior React Developer"
                    value={jobDescription.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    className={cn(getFieldStyling('title'))}
                  />
                </div>
              )}
              
              {renderFieldWithAI('company',
                <div>
                  <label className="text-sm font-medium mb-1 block">Company</label>
                  <Input
                    placeholder="e.g. Tech Innovations Inc."
                    value={jobDescription.company}
                    onChange={(e) => handleInputChange('company', e.target.value)}
                    className={cn(getFieldStyling('company'))}
                  />
                </div>
              )}
              
              {renderFieldWithAI('description',
                <div>
                  <label className="text-sm font-medium mb-1 block">Job Description</label>
                  <Textarea
                    placeholder="Describe the role, responsibilities, and what makes this position exciting..."
                    value={jobDescription.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className={cn("min-h-32", getFieldStyling('description'))}
                  />
                </div>
              )}
            </div>
          </TabsContent>

          {/* Requirements Tab */}
          <TabsContent value="requirements" className="flex-1 space-y-4">
            {renderFieldWithAI('requirements',
              <div>
                <label className="text-sm font-medium mb-1 block">
                  Requirements (one per line)
                </label>
                <Textarea
                  placeholder="e.g.&#10;5+ years experience with React&#10;Strong knowledge of TypeScript&#10;Experience with Next.js"
                  value={jobDescription.requirements.join('\n')}
                  onChange={(e) => handleRequirementsChange(e.target.value)}
                  className={cn("min-h-48", getFieldStyling('requirements'))}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {jobDescription.requirements.length} requirement{jobDescription.requirements.length !== 1 ? 's' : ''} added
                </p>
              </div>
            )}
          </TabsContent>

          {/* Benefits Tab */}
          <TabsContent value="benefits" className="flex-1 space-y-4">
            {renderFieldWithAI('benefits',
              <div>
                <label className="text-sm font-medium mb-1 block">
                  Benefits & Perks (one per line)
                </label>
                <Textarea
                  placeholder="e.g.&#10;Health, dental, and vision insurance&#10;Flexible work schedule&#10;Remote work options&#10;Professional development budget"
                  value={jobDescription.benefits.join('\n')}
                  onChange={(e) => handleBenefitsChange(e.target.value)}
                  className={cn("min-h-48", getFieldStyling('benefits'))}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {jobDescription.benefits.length} benefit{jobDescription.benefits.length !== 1 ? 's' : ''} added
                </p>
              </div>
            )}
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details" className="flex-1 space-y-4">
            <div className="grid gap-4">
              {renderFieldWithAI('location',
                <div>
                  <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Location
                  </label>
                  <Input
                    placeholder="e.g. San Francisco, CA (Remote friendly)"
                    value={jobDescription.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className={cn(getFieldStyling('location'))}
                  />
                </div>
              )}
              
              {renderFieldWithAI('salaryRange',
                <div>
                  <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />
                    Salary Range
                  </label>
                  <Input
                    placeholder="e.g. $120,000 - $150,000"
                    value={jobDescription.salaryRange}
                    onChange={(e) => handleInputChange('salaryRange', e.target.value)}
                    className={cn(getFieldStyling('salaryRange'))}
                  />
                </div>
              )}
              
              {renderFieldWithAI('employmentType',
                <div>
                  <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Employment Type
                  </label>
                  <Input
                    placeholder="e.g. Full-time, Part-time, Contract"
                    value={jobDescription.employmentType}
                    onChange={(e) => handleInputChange('employmentType', e.target.value)}
                    className={cn(getFieldStyling('employmentType'))}
                  />
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <Separator className="my-4" />
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Save className="w-4 h-4" />
            Save Draft
          </Button>
          <Button size="sm" className="flex-1">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default JobDescriptionEditor;