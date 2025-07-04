// Path: apps/frontend/app/dashboard/types.ts
export interface CompanyProfile {
    id: number;
    name: string;
    industry: string | null;
    description: string | null;
    mission: string | null;
    business_model: string | null;
    // Added missing fields required by CompanyProfileCard
    company_size_min: number | null;
    company_size_max: number | null;
}

export interface Job {
    id: number;
    company_id: number;
    company_name: string;
    job_title: string;
    // Added to fix filtering logic
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
    // ... other analysis fields
}

export interface TrackedJob {
    id: number; // The correct primary key
    user_id: number;
    status: string;
    notes: string | null;
    created_at: string;
    updated_at: string;
    is_excited: boolean;
    // Added all missing timestamp fields
    applied_at: string | null;
    first_interview_at: string | null;
    offer_received_at: string | null;
    resolved_at: string | null;
    next_action_at: string | null;
    next_action_notes: string | null;
    
    // Nested objects from the backend
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
  has_completed_onboarding: boolean;
  // ... other profile fields
}

export interface RecommendedJob {
  id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  match_score: number;
  matrix_rating: string | null;
}

export type UpdatePayload = Partial<Omit<TrackedJob, 'id' | 'user_id' | 'job_opportunity' | 'job' | 'company' | 'job_analysis' | 'ai_grade'>>;