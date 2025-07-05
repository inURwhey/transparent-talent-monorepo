// Path: apps/frontend/app/dashboard/types.ts
export interface CompanyProfile {
    id: number;
    name: string;
    industry: string | null;
    description: string | null;
    mission: string | null;
    business_model: string | null;
    company_size_min: number | null;
    company_size_max: number | null;
}

export interface Job {
    id: number;
    company_id: number;
    company_name: string;
    job_title: string;
    status: string;
}

export interface JobOpportunity {
    id: number;
    job_id: number;
    url: string;
    is_active: boolean;
}

export interface AIAnalysis {
    job_id: number;
    user_id: number;
    matrix_rating: string | null;
}

export interface TrackedJob {
    id: number;
    user_id: number;
    status: string;
    notes: string | null;
    created_at: string;
    updated_at: string;
    is_excited: boolean;
    applied_at: string | null;
    first_interview_at: string | null;
    offer_received_at: string | null;
    resolved_at: string | null;
    next_action_at: string | null;
    next_action_notes: string | null;
    job_opportunity: JobOpportunity;
    job: Job;
    company: CompanyProfile | null;
    job_analysis: AIAnalysis | null;
    ai_grade: string | null;
}

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
  // CORRECTED: Added the new optional fields
  disc_assessment?: string | null;
  clifton_strengths?: string | null;
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

export type UpdatePayload = Partial<Omit<TrackedJob, 'id' | 'user_id' | 'job_opportunity' | 'job' | 'company' | 'job_analysis' | 'ai_grade'>>;