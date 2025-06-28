// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';

// --- COMPONENT & UTILITY IMPORTS ---
import { DataTable } from './data-table';
import { getColumns } from './components/columns'; // NEW: Import columns from their own file

// --- TYPE DEFINITIONS ---
interface Profile {
  full_name: string;
  short_term_career_goal: string;
}
interface Job {
  id: number;
  job_title: string;
  company_name: string;
  job_url: string;
}
interface AIAnalysis {
  position_relevance_score: number;
  environment_fit_score: number;
  hiring_manager_view: string;
  matrix_rating: string;
  summary: string;
  qualification_gaps: string[];
  recommended_testimonials: string[];
}
interface TrackedJob {
  tracked_job_id: number;
  job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  status: string;
  user_notes: string | null;
  applied_at: string | null;
  created_at: string; // NEW: The date the job was saved
  ai_analysis: AIAnalysis | null;
}
type UpdatePayload = {
  notes?: string;
  applied_at?: string | null;
  status?: string;
};

export default function UserDashboard() {
  // --- STATE MANAGEMENT ---
  const [profile, setProfile] = useState<Profile | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [debugError, setDebugError] = useState<string | null>(null);
  
  const [jobUrl, setJobUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const { getToken } = useAuth();
  const { user, isLoaded: isUserLoaded } = useUser();

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  // --- DATA FETCHING & MUTATIONS ---
  const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    if (!token) throw new Error("Authentication token is missing.");
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('Content-Type', 'application/json');
    return fetch(url, { ...options, headers });
  }, [getToken]);

  useEffect(() => {
    const fetchDataForPage = async () => {
        try {
          setIsLoading(true);
          const [profileRes, jobsRes, trackedJobsRes] = await Promise.all([
            authedFetch(`${apiBaseUrl}/api/profile`),
            authedFetch(`${apiBaseUrl}/api/jobs`),
            authedFetch(`${apiBaseUrl}/api/tracked-jobs`)
          ]);

          if (!profileRes.ok) throw new Error(`Profile fetch failed`);
          if (!jobsRes.ok) throw new Error(`Jobs fetch failed`);
          if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed`);

          setProfile(await profileRes.json());
          setJobs(await jobsRes.json());
          setTrackedJobs(await trackedJobsRes.json());

        } catch (error: unknown) {
          setDebugError(error instanceof Error ? error.message : "An unknown error occurred.");
        } finally {
          setIsLoading(false);
        }
    };
    if (isUserLoaded) {
      fetchDataForPage();
    }
  }, [isUserLoaded, apiBaseUrl, authedFetch, user]);

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });
      setTrackedJobs(prev => prev.map(job => 
        job.tracked_job_id === trackedJobId ? { ...job, ...payload, user_notes: payload.notes ?? job.user_notes } : job
      ));
    } catch (error) { console.error("Update Error:", error); }
  }, [apiBaseUrl, authedFetch]);

  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (!window.confirm("Are you sure?")) return;
    try {
        await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
        setTrackedJobs(currentJobs => currentJobs.filter(job => job.tracked_job_id !== trackedJobId));
    } catch (error) { console.error("Remove Job Error:", error); }
  }, [apiBaseUrl, authedFetch]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    await handleUpdate(trackedJobId, { status: newStatus });
  }, [handleUpdate]);

  const handleJobSubmit = useCallback(async (event: FormEvent) => {
    event.preventDefault();
    if (!jobUrl.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setSubmissionError(null);
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/jobs/submit`, { method: 'POST', body: JSON.stringify({ job_url: jobUrl }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Failed to submit job.');
      setTrackedJobs(prevJobs => [result, ...prevJobs]);
      setJobUrl('');
    } catch (error) { setSubmissionError(error instanceof Error ? error.message : 'An unknown error.'); } 
    finally { setIsSubmitting(false); }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting]);

  // --- COLUMN DEFINITIONS (NOW CLEANLY HANDLED) ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob }), [handleStatusChange, handleRemoveJob]);

  // --- RENDER LOGIC ---
  if (!isUserLoaded && isLoading) return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>
  if (debugError) return (<div className="min-h-screen flex items-center justify-center text-center"><div><h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2><p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p><p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md"><strong>Error Details:</strong> {debugError}</p></div></div>);
  
  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      {profile && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
              <h1 className="text-3xl font-bold text-gray-800">{profile.full_name}</h1>
              <p className="text-lg text-gray-600 mt-2">Short Term Goal:</p>
              <p className="text-gray-700 italic">{profile.short_term_career_goal || "No goal set."}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Analyze a New Job</h2>
            <form onSubmit={handleJobSubmit}>
              <label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700">Paste Job Posting URL</label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input type="url" name="jobUrl" id="jobUrl" className="block w-full flex-1 rounded-none rounded-l-md border-gray-300 p-2" placeholder="https://www.linkedin.com/jobs/view/..." value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} required />
                <button type="submit" className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300" disabled={isSubmitting}>
                  {isSubmitting ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
              {submissionError && <p className="mt-2 text-sm text-red-600">{submissionError}</p>}
            </form>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
            <DataTable columns={columns} data={trackedJobs} />
          </div>
        </div>
      )}
    </main>
  );
}