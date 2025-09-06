# Smart Hiring Application - Implementation Plan (Phase 1-7)

## Project Overview

**Objective:** Build a smart hiring application with voice-enabled JD creation, intelligent skill matching with context extraction, and comprehensive candidate-job matching using a hybrid LLM + deterministic approach.

### Tech Stack:

- **Frontend:** Next.js 14+ (App Router)
- **Backend:** Next.js API Routes
- **Database:** MongoDB
- **Voice:** Pipecat (existing)
- **LLM:** OpenAI GPT-4 / Claude API
- **File Processing:** pdf-parse, mammoth
- **Cache:** Redis
- **Storage:** AWS S3 / Cloudinary


## Phase 1: Foundation & Infrastructure

**Duration:** Week 1-2  
**Goal:** Set up core infrastructure and basic data models

### 1.1 Project Setup

- Initialize Next.js project with TypeScript
- Configure MongoDB connection with Mongoose
- Set up Redis for caching
- Configure environment variables
- Set up file storage (S3/Cloudinary)

### 1.2 Database Schema Design

```javascript
// Core Collections
- candidates
- jobDescriptions  
- companies
- matchResults
- skills (for taxonomy)
```

### 1.3 Basic API Structure

```
/api/
  ├── upload/
  │   └── resume.ts
  ├── candidates/
  │   ├── create.ts
  │   └── [id].ts
  ├── jobs/
  │   ├── create.ts
  │   └── [id].ts
  └── llm/
      └── process.ts
```

### 1.4 LLM Service Setup

```javascript
// services/llm.service.ts
- Configure OpenAI/Claude client
- Set up retry logic
- Implement rate limiting
- Create prompt templates
```

### Deliverables

- Working MongoDB connection
- Basic API endpoints
- LLM service configured
- File upload working


## Phase 2: Resume Processing Pipeline

**Duration:** Week 2-3  
**Goal:** Build resume parsing and skill extraction with LLM

### 2.1 File Processing

```javascript
// Text extraction from multiple formats
- PDF parsing (pdf-parse)
- DOCX parsing (mammoth)
- Text cleaning and normalization
```

### 2.2 LLM-Based Skill Extraction

```javascript
const resumeExtractionPrompt = `
Extract from resume:
1. Skills with experience years
2. Context where each skill was used
3. Specific work done with each skill
4. Projects and achievements
Output as structured JSON
`;
```

### 2.3 Data Validation & Storage

```javascript
// Validation pipeline
validateLLMOutput() → cleanData() → normalizeSkills() → saveToMongoDB()
```

### 2.4 Fallback Mechanisms

- Regex-based extraction for common patterns
- Manual skill list matching
- Error handling for LLM failures

### API Endpoints

- `POST /api/candidates/upload`
- `POST /api/candidates/extract-skills`
- `GET  /api/candidates/:id/skills`

### Deliverables

- Resume upload and parsing
- Skill extraction with context
- Structured data in MongoDB
- Error handling and validation


## Phase 3: Job Description Processing

**Duration:** Week 3-4  
**Goal:** JD creation interface with voice integration

### 3.1 Voice-Enabled JD Creator UI

```jsx
// Two-panel interface
<VoiceChatPanel /> // Left - Pipecat integration
<JDEditorPanel />   // Right - Live updating
```

### 3.2 JD Templates

```javascript
const templates = {
  'software_engineer': { ... },
  'devops_engineer': { ... },
  'data_scientist': { ... }
}
```

### 3.3 LLM-Based JD Analysis

```javascript
const jdExtractionPrompt = `
Extract requirements:
- Required skills (mandatory vs nice-to-have)
- Experience levels needed
- Specific contexts required
Output as structured JSON
`;
```

### 3.4 WebSocket Integration

- Real-time updates from voice to editor
- Auto-save functionality
- State management (Jotai)

### API Endpoints

- `POST /api/jobs/create`
- `POST /api/jobs/extract-requirements`
- `PUT  /api/jobs/:id`
- `GET  /api/jobs/:id`

### Deliverables

- Voice-enabled JD creator
- Live-updating editor
- Template system
- JD requirement extraction


## Phase 4: Skill Matching Engine

**Duration:** Week 4-5  
**Goal:** Build hybrid matching system with context

### 4.1 Deterministic Matching Core

```javascript
class MatchingEngine {
  // Exact matching
  exactMatch(candidateSkill, requiredSkill)
  
  // Synonym matching
  synonymMatch(skill1, skill2)
  
  // Score calculation
  calculateScore(matched, years, level, mandatory)
}
```

### 4.2 Skill Taxonomy

```javascript
const skillTaxonomy = {
  'JavaScript': ['JS', 'ECMAScript', 'ES6'],
  'Kubernetes': ['K8s', 'K8'],
  'Docker': ['Containerization', 'Containers']
}
```

### 4.3 Context-Aware Matching

```javascript
// For each matched skill, extract relevant context
const matchWithContext = {
  skill: 'Docker',
  matched: true,
  score: 85,
  candidateContext: [...],  // From resume
  requiredContext: '...',   // From JD
  relevanceScore: 0.9
}
```

### 4.4 LLM Summary Generation

```javascript
const generateSummaryPrompt = `
For skill match "${skill}":
Candidate experience: ${contexts}
Write 2-3 specific sentences about what they did
`;
```

### API Endpoints

- `POST /api/matching/run`
- `GET  /api/matching/results/:jobId`
- `POST /api/matching/generate-summary`

### Deliverables

- Skill matching algorithm
- Context extraction for matches
- Match scoring system
- Summary generation for each skill


## Phase 5: Company Intelligence System

**Duration:** Week 5-6  
**Goal:** Company profile matching and web scraping

### 5.1 Company Data Model

```javascript
{
  name: String,
  type: 'startup' | 'enterprise' | 'mid-size',
  industry: String,
  technologies: [String],
  culture: String,
  size: Number
}
```

### 5.2 Web Scraping Service

```javascript
// Data sources
- Company websites
- LinkedIn pages
- Glassdoor reviews
- Crunchbase data
```

### 5.3 Company Profile Matching

```javascript
// Match candidate's past companies with hiring company
calculateCompanyFit(candidateCompanies, targetCompany)
```

### 5.4 Scraping Queue System

```javascript
// BullMQ job queue
- Rate limiting
- Retry logic
- Result caching
```

### API Endpoints

- `POST /api/companies/scrape`
- `GET  /api/companies/:id`
- `PUT  /api/companies/:id/profile`

### Deliverables

- Company data collection
- Profile classification
- Company matching logic
- Scraping infrastructure


## Phase 6: Advanced Matching & Scoring

**Duration:** Week 6-7  
**Goal:** Complete matching algorithm with all factors

### 6.1 Multi-Factor Scoring

```javascript
const overallScore = {
  skillMatch: weight * 0.5,
  companyMatch: weight * 0.3,
  profileMatch: weight * 0.2
}
```

### 6.2 Project-Skill Deep Analysis

```javascript
// Extract what exactly they did with each skill
{
  skill: 'Docker',
  projects: [
    {
      name: 'E-commerce Platform',
      usage: 'Containerized 50+ microservices',
      complexity: 'Advanced',
      impact: '60% deployment time reduction'
    }
  ]
}
```

### 6.3 Experience Level Classification

```javascript
// Classify expertise level from context
classifyExpertise(contexts) {
  // Basic: Used tool
  // Intermediate: Configured/Modified
  // Advanced: Architected/Led
  // Expert: Innovated/Taught
}
```

### 6.4 Comprehensive Report Generation

```javascript
{
  candidate: {...},
  job: {...},
  overallScore: 78,
  breakdown: {
    skills: {...},
    company: {...},
    profile: {...}
  },
  summary: 'Generated by LLM',
  recommendations: [...]
}
```

### Deliverables

- Complete scoring algorithm
- Deep skill analysis
- Expertise classification
- Detailed match reports


## Phase 7: UI/UX Implementation

**Duration:** Week 7-8  
**Goal:** Build user interfaces for all features

### 7.1 Dashboard

```jsx
// Main dashboard components
<ApplicationsList />
<CreateApplicationButton />
<RecentMatches />
<Analytics />
```

### 7.2 JD Creation Interface

```jsx
// Two-panel layout
<div className="grid grid-cols-2">
  <VoiceChatInterface />  // With Pipecat
  <JDEditor />            // Rich text editor
</div>
```

### 7.3 Candidate List & Filtering

```jsx
<CandidateList>
  <FilterPanel />
  <SortOptions />
  <CandidateCard>
    <SkillMatchSummary />
    <ViewDetailsButton />
  </CandidateCard>
</CandidateList>
```

### 7.4 Match Results View

```jsx
<MatchResultsPage>
  <OverallScore />
  <SkillBreakdown>
    <SkillMatch>
      <ContextSummary />
      <Examples />
    </SkillMatch>
  </SkillBreakdown>
  <Recommendations />
</MatchResultsPage>
```

### Deliverables

- Complete UI for all features
- Responsive design
- Real-time updates
- Export functionality


## MongoDB Schemas

### Candidates Collection

```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  phone: String,
  
  // LLM extracted data
  llm_extracted: {
    skills: [{
      name: String,
      years: Number,
      contexts: [String],
      specific_work: String,
      projects: [String]
    }],
    achievements: [String],
    companies: [{
      name: String,
      role: String,
      duration: String
    }]
  },
  
  // Processed and validated data
  processed_skills: [{
    name: String,
    normalized_name: String,
    years: Number,
    contexts: [String],
    proficiency: String
  }],
  
  work_experience: [{
    company: String,
    role: String,
    start_date: Date,
    end_date: Date,
    description: String
  }],
  
  raw_resume_text: String,
  file_url: String,
  created_at: Date,
  updated_at: Date
}
```

### Job Descriptions Collection

```javascript
{
  _id: ObjectId,
  title: String,
  company: String,
  description: String,
  
  // LLM extracted requirements
  llm_extracted: {
    required_skills: [{
      name: String,
      level: String,
      years_required: Number,
      mandatory: Boolean,
      context: String
    }],
    nice_to_have: [String],
    company_type: String,
    domain: String
  },
  
  // Structured requirements
  requirements: {
    skills: [{
      name: String,
      normalized_name: String,
      level: String,
      mandatory: Boolean,
      weight: Number
    }],
    experience_years: Number,
    education: String,
    location: String
  },
  
  template_used: String,
  voice_transcript: String,
  raw_jd_text: String,
  status: String,
  created_by: String,
  created_at: Date,
  updated_at: Date
}
```

### Match Results Collection

```javascript
{
  _id: ObjectId,
  candidate_id: ObjectId,
  job_id: ObjectId,
  
  // Skill matching details
  skill_matches: [{
    skill_name: String,
    matched: Boolean,
    score: Number,
    candidate_years: Number,
    required_level: String,
    candidate_contexts: [String],
    summary: String
  }],
  
  // Company matching
  company_match: {
    score: Number,
    candidate_companies: [String],
    target_company_type: String,
    analysis: String
  },
  
  // Profile matching
  profile_match: {
    score: Number,
    candidate_profile: String,
    required_profile: String,
    analysis: String
  },
  
  // Overall results
  overall_score: Number,
  overall_summary: String,
  recommendations: [String],
  
  // Metadata
  matched_at: Date,
  reviewed: Boolean,
  review_notes: String,
  status: String
}
```

### Companies Collection

```javascript
{
  _id: ObjectId,
  name: String,
  website: String,
  
  // Profile classification
  profile: {
    type: String, // 'startup', 'enterprise', 'mid-size'
    industry: String,
    size: Number,
    founded: Number,
    location: String
  },
  
  // Scraped data
  scraped_data: {
    technologies: [String],
    culture: String,
    recent_news: [Object],
    glassdoor_rating: Number,
    linkedin_data: Object,
    last_scraped: Date
  },
  
  // Manual overrides
  verified: Boolean,
  manual_data: Object,
  
  created_at: Date,
  updated_at: Date
}
```

## Implementation Notes

### Critical Success Factors

- **LLM Prompt Engineering:** Invest time in perfecting prompts for accurate extraction
- **Validation Layer:** Robust validation for all LLM outputs
- **Fallback Mechanisms:** Always have non-LLM alternatives
- **Performance:** Fast matching with good accuracy
- **Cost Control:** Monitor and optimize LLM usage

### Key Technical Decisions

- **Hybrid Approach:** LLM for extraction and understanding, deterministic for matching
- **MongoDB:** Flexible schema for varied resume formats
- **Next.js:** Full-stack framework for rapid development
- **Strategic LLM Use:** Only where it adds clear value
- **Caching Strategy:** Redis for expensive operations

### Development Best Practices

- **Modular Architecture:** Separate concerns for each service
- **Error Handling:** Comprehensive error handling at every layer
- **Testing:** Unit tests for critical logic, integration tests for flows
- **Documentation:** Document all APIs and complex logic
- **Version Control:** Git with feature branches