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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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
  job_posting_status: string;
  last_checked_at: string | null;
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
  is_excited: boolean;
  job_posting_status: string; // Added from 'jobs' table
  last_checked_at: string | null; // Added from 'jobs' table
  status_reason: string | null; // Added for 'tracked_jobs' table
  ai_analysis: AIAnalysis | null;
}
type UpdatePayload = {
  notes?: string | null;
  applied_at?: string | null;
  status?: string;
  is_excited?: boolean;
  status_reason?: string | null;
};

export default function UserDashboard() {
  // --- STATE MANAGEMENT ---
  const [profile, setProfile] = useState<Profile | null>(null);
  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [debugError, setDebugError] = useState<string | null>(null);

  const [jobUrl, setJobUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });
  const [totalFromBackend, setTotalFromBackend] = useState(0);

  const [filterStatus, setFilterStatus] = useState<'all' | 'active_application' | 'expired_application' | 'active_posting' | 'expired_posting'>('all');

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

  const fetchTrackedJobsData = useCallback(async () => {
    // Only set loading to true on the very first fetch
    if (trackedJobs.length === 0) {
      setIsLoading(true);
    }
    try {
      // For this refactor, we will fetch *all* tracked jobs and paginate/filter on the client.
      // This simplifies the logic and removes the API pagination dependency causing the loop.
      // A future optimization could be full server-side pagination.
      const url = `${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`; // Fetch all for client-side handling
      const trackedJobsRes = await authedFetch(url);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed`);

      const data = await trackedJobsRes.json();
      setTrackedJobs(data.tracked_jobs);
      setTotalFromBackend(data.total_count);

    } catch (error: unknown) {
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred while fetching tracked jobs.");
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, authedFetch, trackedJobs.length]); // trackedJobs.length helps with initial isLoading state

  // Initial data fetch for profile and the main tracked jobs list
  useEffect(() => {
    const fetchInitialData = async () => {
      setIsLoading(true);
      try {
        const profileRes = await authedFetch(`${apiBaseUrl}/api/profile`);
        if (!profileRes.ok) throw new Error(`Profile fetch failed`);
        setProfile(await profileRes.json());
        
        // Now fetch tracked jobs
        await fetchTrackedJobsData();

      } catch (error: unknown) {
        setDebugError(error instanceof Error ? error.message : "An unknown error occurred during initial data fetch.");
        setIsLoading(false);
      }
    };
    if (isUserLoaded) {
      fetchInitialData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isUserLoaded, apiBaseUrl, authedFetch]); // fetchTrackedJobsData is now stable enough to be excluded

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      // Optimistically update the UI
      setTrackedJobs(prev => prev.map(job =>
        job.tracked_job_id === trackedJobId
          ? { ...job, ...payload }
          : job
      ));

      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });

      if (!response.ok) {
        // If the update fails, revert the change by re-fetching
        await fetchTrackedJobsData();
        throw new Error(`Failed to update job: ${response.statusText}`);
      }
      // Optionally, update the specific job with the response from the server
      const updatedJobFromServer = await response.json();
      setTrackedJobs(prev => prev.map(job =>
        job.tracked_job_id === trackedJobId ? { ...job, ...updatedJobFromServer } : job
      ));

    } catch (error) {
      console.error("Update Error:", error);
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred during update.");
    }
  }, [apiBaseUrl, authedFetch, fetchTrackedJobsData]);

  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (!window.confirm("Are you sure?")) return;
    
    const originalJobs = trackedJobs;
    // Optimistically remove from UI
    setTrackedJobs(prev => prev.filter(job => job.tracked_job_id !== trackedJobId));

    try {
        const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
        if (!response.ok) {
          // Revert if API call fails
          setTrackedJobs(originalJobs);
        }
    } catch (error) { 
        console.error("Remove Job Error:", error); 
        setTrackedJobs(originalJobs); // Revert on error
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    const currentJob = trackedJobs.find(job => job.tracked_job_id === trackedJobId);
    if (!currentJob) return;

    const payload: UpdatePayload = { status: newStatus };
    if (newStatus === "Applied" && !currentJob.applied_at) {
      payload.applied_at = new Date().toISOString();
    } else if (newStatus !== "Applied" && currentJob.status === "Applied") {
      payload.applied_at = null;
    }
    
    payload.status_reason = currentJob.status === 'Expired' && newStatus !== 'Expired' ? null : currentJob.status_reason;
    await handleUpdate(trackedJobId, payload);
  }, [handleUpdate, trackedJobs]);

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
      
      // Add the new job to the top of the list and reset pagination/filter
      setTrackedJobs(prev => [result, ...prev]);
      setFilterStatus('all');
      setPagination(prev => ({ ...prev, pageIndex: 0 }));
      setJobUrl('');

    } catch (error) { setSubmissionError(error instanceof Error ? error.message : 'An unknown error.'); }
    finally { setIsSubmitting(false); }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting]);

  // --- FILTERING LOGIC ---
  const filteredTrackedJobs = useMemo(() => {
    if (filterStatus === 'all') return trackedJobs;
    return trackedJobs.filter(job => {
      switch (filterStatus) {
        case 'active_application':
          return ['Applied', 'Interviewing', 'Offer'].includes(job.status);
        case 'expired_application':
          return ['Expired', 'Rejected', 'Withdrawn', 'Accepted'].includes(job.status);
        case 'active_posting':
          return job.job_posting_status === 'Active';
        case 'expired_posting':
          return job.job_posting_status !== 'Active';
        default:
          return true;
      }
    });
  }, [trackedJobs, filterStatus]);

  // *** THE FIX: This hook now *only* resets pagination when the filter changes. ***
  useEffect(() => {
    setPagination(prev => ({ ...prev, pageIndex: 0 }));
  }, [filterStatus]);

  // --- COLUMN DEFINITIONS ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]);

  // --- RENDER LOGIC ---
  if (!isUserLoaded) {
    return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>;
  }
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>;
  }
  if (debugError) {
    return (
      <div className="min-h-screen flex items-center justify-center text-center">
        <div>
          <h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2>
          <p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p>
          <p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md">
            <strong>Error Details:</strong> {debugError}
          </p>
        </div>
      </div>
    );
  }

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
            <div className="mb-4">
                <Label htmlFor="filterStatus" className="block text-sm font-medium text-gray-700 mb-1">Filter by Status:</Label>
                <Select value={filterStatus} onValueChange={(value: typeof filterStatus) => setFilterStatus(value)}>
                    <SelectTrigger className="w-[220px]">
                        <SelectValue placeholder="All Jobs" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Jobs</SelectItem>
                        <SelectItem value="active_application">Active Applications</SelectItem>
                        <SelectItem value="expired_application">Expired Applications</SelectItem>
                        <SelectItem value="active_posting">Active Job Postings</SelectItem>
                        <SelectItem value="expired_posting">Expired Job Postings</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <DataTable
              columns={columns}
              data={filteredTrackedJobs}
              pagination={pagination}
              setPagination={setPagination}
              totalCount={filteredTrackedJobs.length} // Pass the dynamic length of the filtered array
            />
          </div>
        </div>
      )}
    </main>
  );
}