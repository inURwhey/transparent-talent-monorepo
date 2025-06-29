// Path: apps/frontend/app/dashboard/types.ts

// Add latitude and longitude to the Profile interface
export interface Profile {
  full_name: string;
  short_term_career_goal: string;
  latitude: number | null;
  longitude: number | null;
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

export type UpdatePayload = Partial<Omit<TrackedJob, 'tracked_job_id' | 'job_id' | 'job_title' | 'company_name' | 'job_url' | 'created_at' | 'job_posting_status' | 'last_checked_at' | 'ai_analysis'>>;