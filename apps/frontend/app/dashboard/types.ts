// Path: apps/frontend/app/dashboard/types.ts

// The Profile interface is now significantly expanded
export interface Profile {
  id: number;
  user_id: number;
  full_name: string | null;
  current_location: string | null;
  latitude: number | null;
  longitude: number | null;
  linkedin_profile_url: string | null;
  resume_url: string | null;
  short_term_career_goal: string | null;
  long_term_career_goals: string | null;
  // Removed old desired_annual_compensation: string | null;
  desired_salary_min: number | null; // New structured salary field
  desired_salary_max: number | null; // New structured salary field
  desired_title: string | null;
  ideal_role_description: string | null;
  preferred_company_size: string | null;
  ideal_work_culture: string | null;
  disliked_work_culture: string | null;
  core_strengths: string | null;
  skills_to_avoid: string | null;
  non_negotiable_requirements: string | null;
  deal_breakers: string | null;
  preferred_industries: string | null;
  industries_to_avoid: string | null;
  personality_adjectives: string | null;
  personality_16_personalities: string | null;
  personality_disc: string | null;
  personality_gallup_strengths: string | null;
  preferred_work_style: 'On-site' | 'Remote' | 'Hybrid' | null;
  is_remote_preferred: boolean | null;

  // --- NEW "LAYER 3" FIELDS ---
  has_completed_onboarding: boolean;
  work_style_preference: string | null;
  conflict_resolution_style: string | null;
  communication_preference: string | null;
  change_tolerance: string | null;
}

export interface AIAnalysis {
  position_relevance_score: number;
  environment_fit_score: number;
  hiring_manager_view: string;
  matrix_rating: string;
  summary: string;
  qualification_gaps: string[];
  recommended_testimonials: string[];
}

export interface TrackedJob {
  tracked_job_id: number;
  job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  status: string;
  user_notes: string | null;
  created_at: string;
  is_excited: boolean;
  job_posting_status: string;
  last_checked_at: string | null;
  status_reason: string | null;
  applied_at: string | null;
  first_interview_at: string | null;
  offer_received_at: string | null;
  resolved_at: string | null;
  next_action_at: string | null;
  next_action_notes: string | null;
  ai_analysis: AIAnalysis | null;
}

// --- NEW INTERFACE FOR JOB RECOMMENDATIONS ---
export interface RecommendedJob {
  id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  match_score: number;
  job_modality: string | null;
  deduced_job_level: string | null;
}

export type UpdatePayload = Partial<Omit<TrackedJob, 'tracked_job_id' | 'job_id' | 'job_title' | 'company_name' | 'job_url' | 'created_at' | 'job_posting_status' | 'last_checked_at' | 'ai_analysis'>>;