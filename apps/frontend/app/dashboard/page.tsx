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
  const [jobs, setJobs] = useState<Job[]>([]);
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
  const [totalTrackedJobsCount, setTotalTrackedJobsCount] = useState(0);

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
    try {
      setIsLoading(true);
      const { pageIndex, pageSize } = pagination;
      const url = `${apiBaseUrl}/api/tracked-jobs?page=${pageIndex + 1}&limit=${pageSize}`;
      const trackedJobsRes = await authedFetch(url);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed`);

      const data = await trackedJobsRes.json();
      setTrackedJobs(data.tracked_jobs);
      // Note: totalTrackedJobsCount here is the backend's total count *before* client-side filtering.
      // The filtered count for pagination will be set locally.
      setTotalTrackedJobsCount(data.total_count); 

    } catch (error: unknown) {
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred while fetching tracked jobs.");
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, authedFetch, pagination]);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
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
    };
    if (isUserLoaded) {
        fetchInitialData();
    }
  }, [isUserLoaded, apiBaseUrl, authedFetch]);

  useEffect(() => {
    if (isUserLoaded) {
      fetchTrackedJobsData();
    }
  }, [isUserLoaded, fetchTrackedJobsData]);

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      const optimisticUpdate: Partial<TrackedJob> = {};
      if (payload.status !== undefined) optimisticUpdate.status = payload.status;
      if (payload.notes !== undefined) optimisticUpdate.user_notes = payload.notes;
      if (payload.applied_at !== undefined) optimisticUpdate.applied_at = payload.applied_at;
      if (payload.is_excited !== undefined) optimisticUpdate.is_excited = payload.is_excited;
      if (payload.status_reason !== undefined) optimisticUpdate.status_reason = payload.status_reason;

      setTrackedJobs(prev => prev.map(job =>
        job.tracked_job_id === trackedJobId
          ? { ...job, ...optimisticUpdate }
          : job
      ));

      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });

      if (!response.ok) {
        await fetchTrackedJobsData();
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
        await fetchTrackedJobsData();
    } catch (error) { console.error("Remove Job Error:", error); }
  }, [apiBaseUrl, authedFetch, fetchTrackedJobsData]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    const currentJob = trackedJobs.find(job => job.tracked_job_id === trackedJobId);
    if (!currentJob) {
      console.error(`Job with ID ${trackedJobId} not found.`);
      return;
    }

    const payload: UpdatePayload = { status: newStatus };
    let newStatusReason: string | null = currentJob.status_reason;

    if (newStatus === "Applied" && !currentJob.applied_at) {
      payload.applied_at = new Date().toISOString().split('T')[0];
    } else if (newStatus !== "Applied" && currentJob.applied_at) {
      payload.applied_at = null;
    }

    if (currentJob.status === 'Expired' && newStatus !== 'Expired') {
        newStatusReason = null;
    } else if (newStatus === 'Expired' && currentJob.status !== 'Expired') {
        newStatusReason = 'Manually expired by user';
    }
    payload.status_reason = newStatusReason;

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

      setPagination(prev => ({ ...prev, pageIndex: 0 }));
      setJobUrl('');

    } catch (error) { setSubmissionError(error instanceof Error ? error.message : 'An unknown error.'); }
    finally { setIsSubmitting(false); }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting, setPagination]);

  // --- FILTERING LOGIC ---
  const filteredTrackedJobs = useMemo(() => {
    let filtered = trackedJobs;
    if (filterStatus === 'active_application') {
      // Define active applications as those actively in the pipeline
      filtered = trackedJobs.filter(job => ['Applied', 'Interviewing', 'Offer'].includes(job.status));
    } else if (filterStatus === 'expired_application') {
      // Define expired applications as those no longer active in the pipeline
      filtered = trackedJobs.filter(job => ['Expired', 'Rejected', 'Withdrawn', 'Accepted'].includes(job.status));
    } else if (filterStatus === 'active_posting') {
      filtered = trackedJobs.filter(job => job.job_posting_status === 'Active');
    } else if (filterStatus === 'expired_posting') {
      filtered = trackedJobs.filter(job => job.job_posting_status !== 'Active');
    }
    return filtered;
  }, [trackedJobs, filterStatus]);

  // Update total count and reset pagination when filter changes
  useEffect(() => {
    setTotalTrackedJobsCount(filteredTrackedJobs.length);
    setPagination(prev => ({ ...prev, pageIndex: 0 }));
  }, [filteredTrackedJobs, setTotalTrackedJobsCount, setPagination, filterStatus]); // Add filterStatus to dependencies

  // --- COLUMN DEFINITIONS ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]);

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
              totalCount={totalTrackedJobsCount} {/* This will now reflect the filtered count */}
            />
          </div>
        </div>
      )}
    </main>
  );
}