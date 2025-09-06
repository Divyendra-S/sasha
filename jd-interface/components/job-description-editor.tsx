"use client";

import { useAtom, useSetAtom } from "jotai";
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
  Download
} from "lucide-react";

export function JobDescriptionEditor() {
  const [jobDescription] = useAtom(jobDescriptionAtom);
  const updateJD = useSetAtom(updateJDAtom);

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

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            <CardTitle className="text-lg">Job Description</CardTitle>
          </div>
          <div className="flex items-center gap-2">
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
              <div>
                <label className="text-sm font-medium mb-1 block">Job Title</label>
                <Input
                  placeholder="e.g. Senior React Developer"
                  value={jobDescription.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-1 block">Company</label>
                <Input
                  placeholder="e.g. Tech Innovations Inc."
                  value={jobDescription.company}
                  onChange={(e) => handleInputChange('company', e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-1 block">Job Description</label>
                <Textarea
                  placeholder="Describe the role, responsibilities, and what makes this position exciting..."
                  value={jobDescription.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="min-h-32"
                />
              </div>
            </div>
          </TabsContent>

          {/* Requirements Tab */}
          <TabsContent value="requirements" className="flex-1 space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">
                Requirements (one per line)
              </label>
              <Textarea
                placeholder="e.g.&#10;5+ years experience with React&#10;Strong knowledge of TypeScript&#10;Experience with Next.js"
                value={jobDescription.requirements.join('\n')}
                onChange={(e) => handleRequirementsChange(e.target.value)}
                className="min-h-48"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {jobDescription.requirements.length} requirement{jobDescription.requirements.length !== 1 ? 's' : ''} added
              </p>
            </div>
          </TabsContent>

          {/* Benefits Tab */}
          <TabsContent value="benefits" className="flex-1 space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">
                Benefits & Perks (one per line)
              </label>
              <Textarea
                placeholder="e.g.&#10;Health, dental, and vision insurance&#10;Flexible work schedule&#10;Remote work options&#10;Professional development budget"
                value={jobDescription.benefits.join('\n')}
                onChange={(e) => handleBenefitsChange(e.target.value)}
                className="min-h-48"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {jobDescription.benefits.length} benefit{jobDescription.benefits.length !== 1 ? 's' : ''} added
              </p>
            </div>
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details" className="flex-1 space-y-4">
            <div className="grid gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  Location
                </label>
                <Input
                  placeholder="e.g. San Francisco, CA (Remote friendly)"
                  value={jobDescription.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  Salary Range
                </label>
                <Input
                  placeholder="e.g. $120,000 - $150,000"
                  value={jobDescription.salaryRange}
                  onChange={(e) => handleInputChange('salaryRange', e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-1 block flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Employment Type
                </label>
                <Input
                  placeholder="e.g. Full-time, Part-time, Contract"
                  value={jobDescription.employmentType}
                  onChange={(e) => handleInputChange('employmentType', e.target.value)}
                />
              </div>
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