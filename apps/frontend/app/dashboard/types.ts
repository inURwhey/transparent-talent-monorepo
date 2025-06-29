// Path: apps/frontend/app/dashboard/types.ts

export interface Profile {
  full_name: string;
  short_term_career_goal: string;
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
  applied_at: string | null;
  created_at: string;
  is_excited: boolean;
  job_posting_status: string;
  last_checked_at: string | null;
  status_reason: string | null;
  ai_analysis: AIAnalysis | null;
}

export type UpdatePayload = {
  notes?: string | null;
  applied_at?: string | null;
  status?: string;
  is_excited?: boolean;
  status_reason?: string | null;
};