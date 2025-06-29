// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea'; // Assuming Textarea is available or we'll use a basic <textarea>
import { Label } from '@/components/ui/label'; // Assuming Label is available
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'; // Assuming Select is available

// --- TYPE DEFINITIONS ---
// This interface should accurately reflect all nullable fields as text | null
interface Profile {
    id: number;
    user_id: number;
    full_name: string | null;
    current_location: string | null;
    linkedin_profile_url: string | null;
    resume_url: string | null;
    short_term_career_goal: string | null;
    long_term_career_goals: string | null;
    desired_annual_compensation: string | null;
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
}

// Define the shape of the data that can be sent to the PUT endpoint
type ProfileUpdatePayload = Partial<Omit<Profile, 'id' | 'user_id' | 'resume_url'>>;


export default function UserProfilePage() {
    const router = useRouter();
    const { getToken, isLoaded: isAuthLoaded } = useAuth();
    const { user, isLoaded: isUserLoaded } = useUser();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    const [profile, setProfile] = useState<Profile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    // Fetch user profile on component mount
    useEffect(() => {
        const fetchProfile = async () => {
            if (!isUserLoaded || !isAuthLoaded) return;
            setIsLoading(true);
            setError(null);
            try {
                const response = await authedFetch(`${apiBaseUrl}/api/profile`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to fetch profile.');
                }
                const data: Profile = await response.json();
                setProfile(data);
            } catch (err: any) {
                console.error("Profile fetch error:", err);
                setError(err.message || "An unexpected error occurred.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfile();
    }, [isUserLoaded, isAuthLoaded, apiBaseUrl, authedFetch]);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { id, value } = e.target;
        setProfile(prev => {
            if (!prev) return null;
            return { ...prev, [id]: value === '' ? null : value }; // Store empty strings as null in state
        });
    }, []);

    const handleSelectChange = useCallback((id: keyof Profile, value: string) => {
        setProfile(prev => {
            if (!prev) return null;
            return { ...prev, [id]: value === 'null' ? null : value }; // 'null' string from select becomes actual null
        });
    }, []);
    
```tsx
// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { PaginationState } from '@tanstack/react-table'; // Import PaginationState
import Link from 'next/link'; // Import Link

// --- COMPONENT & UTILITY IMPORTS ---
import { DataTable } from './data-table';
import { getColumns } from './components/columns'; // NEW: Import columns from their own file
import { Button } from '@/components/ui/button'; // Ensure Button is imported

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
// Corrected UpdatePayload to allow null for notes
type UpdatePayload = {
  notes?: string | null; // Allow notes to be null for clearing, or string for updating
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
  }, [apiBaseUrl, authedFetch, pagination]); // Depend on pagination state

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
  }, [isUserLoaded, fetchTrackedJobsData]); // Only re-run when pagination or authedFetch (due to getToken) changes

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      // Optimistic UI update logic remains the same
      const optimisticUpdate: Partial<TrackedJob> = {};
      if (payload.status !== undefined) optimisticUpdate.status = payload.status;
      if (payload.notes !== undefined) optimisticUpdate.user_notes = payload.notes;
      if (payload.applied_at !== undefined) optimisticUpdate.applied_at = payload.applied_at;

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
  }, [apiBaseUrl, authedFetch, fetchTrackedJobsData]); // Add fetchTrackedJobsData to dependencies

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
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting, setPagination]); // Add setPagination to dependencies

  // --- COLUMN DEFINITIONS (NOW CLEANLY HANDLED) ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob }), [handleStatusChange, handleRemoveJob]);

  // --- RENDER LOGIC ---
  if (!isUserLoaded) return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>
  // isLoading only blocks if trackedJobs are loading (after initial profile/jobs fetch)
  // or initial fetch is happening
  if (isLoading && trackedJobs.length === 0 && totalTrackedJobsCount === 0) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>
  if (debugError) return (<div className="min-h-screen flex items-center justify-center text-center"><div><h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2><p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p><p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md"><strong>Error Details:</strong> {debugError}</p></div></div>);
  
  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      {profile && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-md mb-8 flex justify-between items-center"> {/* Added flex layout */}
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