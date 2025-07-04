// Path: apps/frontend/app/dashboard/types.ts

// --- CORE BACKEND MODELS ---
// These interfaces now match the backend's to_dict() methods exactly.

// CORRECTED: Renamed 'Company' to 'CompanyProfile' to match its usage in hooks and components.
export interface CompanyProfile { 
    id: number;
    name: string;
    industry: string | null;
    description: string | null;
    mission: string | null;
    business_model: string | null;
    // ... add other company fields if needed by the UI
}

export interface Job {
    id: number;
    company_id: number;
    company_name: string;
    job_title: string;
    // ... add other job fields if needed by the UI
}

export interface JobOpportunity {
    id: number;
    job_id: number;
    url: string;
    is_active: boolean;
    // ... add other job opportunity fields if needed
}

export interface AIAnalysis {
    job_id: number;
    user_id: number;
    position_relevance_score: number | null;
    environment_fit_score: number | null;
    hiring_manager_view: string | null;
    matrix_rating: string | null;
    summary: string | null;
    qualification_gaps: string[] | null;
    recommended_testimonials: string[] | null;
}

export interface TrackedJob {
    id: number; // The primary key for the tracked_jobs table
    user_id: number;
    job_opportunity_id: number;
    status: string;
    notes: string | null;
    created_at: string;
    updated_at: string;
    is_excited: boolean;
    applied_at: string | null;
    next_action_at: string | null;
    next_action_notes: string | null;
    // --- NESTED OBJECTS FROM THE BACKEND ---
    job_opportunity: JobOpportunity;
    job: Job;
    company: CompanyProfile | null; // This now correctly references the renamed CompanyProfile
    job_analysis: AIAnalysis | null;
    ai_grade: string | null; // This is a convenience property added by the service
}


// --- PROFILE & OTHER UI-SPECIFIC TYPES ---

export interface Profile {
  id: number;
  user_id: number;
  full_name: string | null;
  location: string | null;
  latitude: number | null;
  longitude: number | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  current_role: string | null;
  desired_job_titles: string | null;
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  target_industries: string | null;
  career_goals: string | null;
  preferred_company_size: string | null;
  work_style_preference: string | null;
  conflict_resolution_style: string | null;
  communication_preference: string | null;
  change_tolerance: string | null;
  preferred_work_style: string | null;
  is_remote_preferred: boolean | null;
  skills: string | null;
  education: string | null;
  work_experience: string | null;
  personality_16_personalities: string | null;
  other_personal_attributes: string | null;
  has_completed_onboarding: boolean;
}

export interface RecommendedJob {
  id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  match_score: number;
  matrix_rating: string | null;
  job_modality: string | null;
  deduced_job_level: string | null;
}

// UpdatePayload is used for sending updates. It can be a partial of any top-level TrackedJob field.
export type UpdatePayload = Partial<Omit<TrackedJob, 'job_opportunity' | 'job' | 'company' | 'job_analysis' | 'ai_grade'>>;