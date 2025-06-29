// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { PaginationState } from '@tanstack/react-table';
import Link from 'next/link';

// --- COMPONENT & UTILITY IMPORTS ---
import { DataTable } from './data-table';
import { getColumns } from './components/columns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

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
  created_at: string; // The date the job was saved
  is_excited: boolean; // ADDED: New field for 'Excited?' column
  ai_analysis: AIAnalysis | null;
}
// Corrected UpdatePayload to allow null for notes and include is_excited
type UpdatePayload = {
  notes?: string | null;
  applied_at?: string | null;
  status?: string;
  is_excited?: boolean; // ADDED: Allow updating is_excited
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

  // New pagination state
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0, // TanStack Table uses 0-indexed pageIndex
    pageSize: 10, // Default page size
  });
  const [totalTrackedJobsCount, setTotalTrackedJobsCount] = useState(0); // Total count for pagination controls

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

  // Updated fetch function for tracked jobs to include pagination
  const fetchTrackedJobsData = useCallback(async () => {
    try {
      setIsLoading(true);
      const { pageIndex, pageSize } = pagination;
      // Convert 0-indexed pageIndex to 1-indexed 'page' for the backend
      const url = `${apiBaseUrl}/api/tracked-jobs?page=${pageIndex + 1}&limit=${pageSize}`;
      const trackedJobsRes = await authedFetch(url);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed`);

      const data = await trackedJobsRes.json();
      setTrackedJobs(data.tracked_jobs);
      setTotalTrackedJobsCount(data.total_count);

    } catch (error: unknown) {
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred while fetching tracked jobs.");
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, authedFetch, pagination]);

  // Effect for initial profile and general jobs (not paginated)
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true); // Set loading to true initially for the entire dashboard
        const [profileRes, jobsRes] = await Promise.all([
          authedFetch(`${apiBaseUrl}/api/profile`),
          authedFetch(`${apiBaseUrl}/api/jobs`)
        ]);

        if (!profileRes.ok) throw new Error(`Profile fetch failed`);
        if (!jobsRes.ok) throw new Error(`Jobs fetch failed`);

        setProfile(await profileRes.json());
        setJobs(await jobsRes.json());

      } catch (error: unknown) {
        setDebugError(error instanceof Error ? error.message : "An unknown error occurred during initial data fetch.");
      }
      // Do not set isLoading to false here; it will be handled by fetchTrackedJobsData
    };
    if (isUserLoaded) {
        fetchInitialData();
    }
  }, [isUserLoaded, apiBaseUrl, authedFetch]);


  // Effect for fetching paginated tracked jobs whenever pagination state changes
  useEffect(() => {
    if (isUserLoaded) {
      fetchTrackedJobsData();
    }
  }, [isUserLoaded, fetchTrackedJobsData]);

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      // Optimistic UI update
      const optimisticUpdate: Partial<TrackedJob> = {};
      if (payload.status !== undefined) optimisticUpdate.status = payload.status;
      if (payload.notes !== undefined) optimisticUpdate.user_notes = payload.notes;
      if (payload.applied_at !== undefined) optimisticUpdate.applied_at = payload.applied_at;
      if (payload.is_excited !== undefined) optimisticUpdate.is_excited = payload.is_excited; // ADDED: Optimistic update for is_excited

      setTrackedJobs(prev => prev.map(job =>
        job.tracked_job_id === trackedJobId
          ? { ...job, ...optimisticUpdate }
          : job
      ));

      // Send the original payload to the backend
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });

      if (!response.ok) {
        // If update fails, revert the UI by refetching the specific job or the entire paginated list
        await fetchTrackedJobsData(); // Re-fetch current page after failed update
        throw new Error(`Failed to update job: ${response.statusText}`);
      }

    } catch (error) {
      console.error("Update Error:", error);
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred during update.");
    }
  }, [apiBaseUrl, authedFetch, fetchTrackedJobsData]);

  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (!window.confirm("Are you sure?")) return;
    try {
        await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
        // After deletion, re-fetch the current page to ensure correct pagination display
        await fetchTrackedJobsData();
    } catch (error) { console.error("Remove Job Error:", error); }
  }, [apiBaseUrl, authedFetch, fetchTrackedJobsData]);

  // Modified handleStatusChange to include auto-setting applied_at
  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    const currentJob = trackedJobs.find(job => job.tracked_job_id === trackedJobId);
    if (!currentJob) {
      console.error(`Job with ID ${trackedJobId} not found.`);
      return;
    }

    const payload: UpdatePayload = { status: newStatus };

    // If status is changing to "Applied" and applied_at is not already set
    if (newStatus === "Applied" && !currentJob.applied_at) {
      payload.applied_at = new Date().toISOString().split('T')[0]; // Format as YYYY-MM-DD
    } else if (newStatus !== "Applied" && currentJob.applied_at) {
      // Optional: If status changes from "Applied" to something else and applied_at is set, clear applied_at
      payload.applied_at = null;
    }

    await handleUpdate(trackedJobId, payload);
  }, [handleUpdate, trackedJobs]);

  // ADDED: New handler for toggling 'is_excited'
  const handleToggleExcited = useCallback(async (trackedJobId: number, isExcited: boolean) => {
    await handleUpdate(trackedJobId, { is_excited: isExcited });
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

      // Reset pagination to first page and re-fetch to show the new job
      setPagination(prev => ({ ...prev, pageIndex: 0 }));
      setJobUrl(''); // Clear the input field

    } catch (error) { setSubmissionError(error instanceof Error ? error.message : 'An unknown error.'); }
    finally { setIsSubmitting(false); }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting, setPagination]);

  // --- COLUMN DEFINITIONS (NOW CLEANLY HANDLED) ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]); // ADDED: Pass handleToggleExcited

  // --- RENDER LOGIC ---
  if (!isUserLoaded) return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>
  if (isLoading && trackedJobs.length === 0 && totalTrackedJobsCount === 0) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>
  if (debugError) return (<div className="min-h-screen flex items-center justify-center text-center"><div><h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2><p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p><p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md"><strong>Error Details:</strong> {debugError}</p></div></div>);

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      {profile && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-md mb-8 flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-800">{profile.full_name || 'Your Dashboard'}</h1>
                <p className="text-lg text-gray-600 mt-2">Short Term Goal:</p>
                <p className="text-gray-700 italic">{profile.short_term_career_goal || "No goal set."}</p>
              </div>
              <Link href="/dashboard/profile" passHref>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                  Edit Profile
                </Button>
              </Link>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Analyze a New Job</h2>
            <form onSubmit={handleJobSubmit}>
              <Label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700">Paste Job Posting URL</Label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <Input type="url" name="jobUrl" id="jobUrl" className="block w-full flex-1 rounded-none rounded-l-md border-gray-300 p-2" placeholder="https://www.linkedin.com/jobs/view/..." value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} required />
                <Button type="submit" className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300" disabled={isSubmitting}>
                  {isSubmitting ? 'Analyzing...' : 'Analyze'}
                </Button>
              </div>
              {submissionError && <p className="mt-2 text-sm text-red-600">{submissionError}</p>}
            </form>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
            <DataTable
              columns={columns}
              data={trackedJobs}
              pagination={pagination}
              setPagination={setPagination}
              totalCount={totalTrackedJobsCount}
            />
          </div>
        </div>
      )}
    </main>
  );
}