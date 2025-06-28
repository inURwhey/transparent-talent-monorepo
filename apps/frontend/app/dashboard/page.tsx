// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';

// --- TANSTACK TABLE & UI IMPORTS ---
import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { DataTable } from './data-table';


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
  job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  tracked_job_id: number;
  status: string;
  user_notes: string | null;
  applied_at: string | null;
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
  const [editingJobId, setEditingJobId] = useState<number | null>(null);
  const [editNotes, setEditNotes] = useState('');
  const [editDate, setEditDate] = useState('');
  const [debugError, setDebugError] = useState<string | null>(null);
  
  const [jobUrl, setJobUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const { getToken } = useAuth();
  const { user, isLoaded: isUserLoaded } = useUser();

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('Content-Type', 'application/json');
    return fetch(url, { ...options, headers });
  }, [getToken]);

  // --- INSTRUMENTED DATA FETCHING LOGIC ---
  const fetchDataForPage = useCallback(async () => {
    console.log("DEBUG: fetchDataForPage triggered.");

    if (!isUserLoaded || !user) {
        console.log("DEBUG: Aborting fetch, user not loaded yet.");
        return;
    }
    
    try {
      console.log("DEBUG: Starting data fetch sequence.");
      setDebugError(null);
      setIsLoading(true);

      if (!apiBaseUrl) {
          throw new Error("NEXT_PUBLIC_API_BASE_URL is not set.");
      }
      console.log(`DEBUG: API Base URL is ${apiBaseUrl}`);
      
      const endpoints = {
        profile: `${apiBaseUrl}/api/profile`,
        jobs: `${apiBaseUrl}/api/jobs`,
        trackedJobs: `${apiBaseUrl}/api/tracked-jobs`,
      };

      console.log("DEBUG: Fetching from endpoints:", endpoints);

      const [profileRes, jobsRes, trackedJobsRes] = await Promise.all([
        authedFetch(endpoints.profile),
        authedFetch(endpoints.jobs),
        authedFetch(endpoints.trackedJobs)
      ]);

      console.log("DEBUG: All fetch promises resolved. Responses:", { profileRes, jobsRes, trackedJobsRes });

      if (!profileRes.ok) throw new Error(`Profile fetch failed: ${profileRes.status} ${profileRes.statusText}`);
      if (!jobsRes.ok) throw new Error(`Jobs fetch failed: ${jobsRes.status} ${jobsRes.statusText}`);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed: ${trackedJobsRes.status} ${trackedJobsRes.statusText}`);
      
      console.log("DEBUG: All responses are OK. Parsing JSON...");

      const profileData = await profileRes.json();
      console.log("DEBUG: Parsed profile data:", profileData);

      const jobsData = await jobsRes.json();
      console.log("DEBUG: Parsed jobs data:", jobsData);

      const trackedJobsData = await trackedJobsRes.json();
      console.log("DEBUG: Parsed tracked jobs data:", trackedJobsData);

      console.log("DEBUG: Setting state with parsed data.");
      setProfile(profileData);
      setJobs(jobsData);
      setTrackedJobs(trackedJobsData);
      console.log("DEBUG: State setting complete.");

    } catch (error: unknown) {
      console.error("DEBUG: A critical error was caught in fetchDataForPage:", error);
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred.");
    } finally {
      console.log("DEBUG: 'finally' block reached. Setting isLoading to false.");
      setIsLoading(false);
    }
  }, [apiBaseUrl, isUserLoaded, user, authedFetch]);

  useEffect(() => {
    console.log("DEBUG: useEffect for fetchDataForPage triggered.");
    fetchDataForPage();
  }, [fetchDataForPage]);


  const handleJobSubmit = useCallback(async (event: FormEvent) => {
    event.preventDefault();
    if (!jobUrl.trim() || isSubmitting) return;

    setSubmissionError(null);
    setIsSubmitting(true);

    try {
      const response = await authedFetch(`${apiBaseUrl}/api/jobs/submit`, {
        method: 'POST',
        body: JSON.stringify({ job_url: jobUrl }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || 'Failed to submit job for analysis.');
      }
      setTrackedJobs(prevJobs => [result, ...prevJobs]);
      setJobUrl('');
    } catch (error: unknown) {
      console.error("Job Submission Error:", error);
      setSubmissionError(error instanceof Error ? error.message : 'An unknown error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting]);

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error('Failed to update.');
      fetchDataForPage(); 
      return true;
    } catch (error) {
      console.error("Update Error:", error);
      return false;
    }
  }, [apiBaseUrl, authedFetch, fetchDataForPage]);

  const handleTrackJob = useCallback(async (jobId: number) => {
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs`, {
        method: 'POST', body: JSON.stringify({ job_id: jobId }),
      });
      if (!response.ok) throw new Error('Failed to track job.');
      alert("Job tracked successfully!");
      fetchDataForPage();
    } catch (error) {
      console.error("Tracking Error:", error);
      alert("Could not track the job.");
    }
  }, [apiBaseUrl, authedFetch, fetchDataForPage]);
  
  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (!window.confirm("Are you sure?")) return;
    try {
        const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to remove job.');
        setTrackedJobs(currentJobs => currentJobs.filter(job => job.tracked_job_id !== trackedJobId));
    } catch (error) {
        console.error("Remove Job Error:", error);
        alert("Could not remove the job.");
    }
  }, [apiBaseUrl, authedFetch]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    await handleUpdate(trackedJobId, { status: newStatus });
  }, [handleUpdate]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC'
    });
  }

  // --- COLUMN DEFINITIONS FOR THE DATA TABLE ---
  const columns: ColumnDef<TrackedJob>[] = useMemo(() => [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "job_title",
      header: "Job",
      cell: ({ row }) => {
        const job = row.original;
        return (
          <div className="font-medium">
            {job.job_title}
            <div className="text-sm text-muted-foreground">{job.company_name}</div>
          </div>
        );
      },
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const job = row.original;
        return (
          <select 
            value={job.status} 
            onChange={(e) => handleStatusChange(job.tracked_job_id, e.target.value)}
            onClick={(e) => e.stopPropagation()} // prevent row selection on click
            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg p-2 h-fit focus:ring-blue-500 focus:border-blue-500">
            <option value="Saved">Saved</option>
            <option value="Applied">Applied</option>
            <option value="Interviewing">Interviewing</option>
            <option value="Offer">Offer</option>
            <option value="Rejected">Rejected</option>
          </select>
        );
      }
    },
    {
        accessorKey: "relevance_score",
        header: ({ column }) => {
            return (
              <Button
                variant="ghost"
                onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              >
                Relevance
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            )
        },
        cell: ({row}) => {
            const analysis = row.original.ai_analysis;
            if (!analysis || analysis.position_relevance_score == null || analysis.environment_fit_score == null) {
                return <div className="text-center text-muted-foreground">-</div>;
            }
            const score = analysis.position_relevance_score + analysis.environment_fit_score;
            return <div className="text-center font-medium">{score}</div>
        },
        sortingFn: (rowA, rowB) => {
            const analysisA = rowA.original.ai_analysis;
            const analysisB = rowB.original.ai_analysis;
            const scoreA = (analysisA && analysisA.position_relevance_score != null && analysisA.environment_fit_score != null) 
                         ? analysisA.position_relevance_score + analysisA.environment_fit_score 
                         : -1;
            const scoreB = (analysisB && analysisB.position_relevance_score != null && analysisB.environment_fit_score != null)
                         ? analysisB.position_relevance_score + analysisB.environment_fit_score
                         : -1;
            return scoreA - scoreB;
        }
    },
    {
      accessorKey: "applied_at",
      header: ({ column }) => (
        <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
          Applied Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => formatDate(row.original.applied_at),
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const job = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(job.job_title)}>
                Copy Title
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => window.open(job.job_url, '_blank')}
              >
                View Original Post
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-red-600 focus:text-red-700 focus:bg-red-50"
                onClick={() => handleRemoveJob(job.tracked_job_id)}
              >
                Remove Job
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ], [handleStatusChange, handleRemoveJob, handleUpdate, fetchDataForPage]);


  // --- RENDER LOGIC ---
  if (!isUserLoaded) {
     return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>
  }
  
  if (isLoading) {
     return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
       <div className="max-w-7xl mx-auto p-4 mb-4 border-2 border-dashed border-blue-500 bg-blue-50">
        <h2 className="font-bold text-blue-700">Debug Information</h2>
        <p><strong>User Status:</strong> {isUserLoaded && user ? `Loaded (${user.primaryEmailAddress?.emailAddress})` : `Loading...`}</p>
        <p><strong>API Base URL:</strong> {apiBaseUrl || <span className="font-bold text-red-600">NOT SET</span>}</p>
        {debugError && <p><strong>Caught Error:</strong> <span className="font-bold text-red-600">{debugError}</span></p>}
      </div>
      
      {!debugError && profile ? (
        <div className="max-w-7xl mx-auto">
          {/* ... Profile Section ... */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
              <h1 className="text-3xl font-bold text-gray-800">{profile.full_name}</h1>
              <p className="text-lg text-gray-600 mt-2">Short Term Goal:</p>
              <p className="text-gray-700 italic">{profile.short_term_career_goal || "No goal set."}</p>
          </div>
          
          {/* --- NEW JOB SUBMISSION FORM --- */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Analyze a New Job</h2>
            <form onSubmit={handleJobSubmit}>
              <label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700">
                Paste Job Posting URL
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  type="url"
                  name="jobUrl"
                  id="jobUrl"
                  className="block w-full flex-1 rounded-none rounded-l-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
                  placeholder="https://www.linkedin.com/jobs/view/..."
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                  required
                />
                <button
                  type="submit"
                  className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:bg-indigo-300 disabled:cursor-not-allowed"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
              {submissionError && <p className="mt-2 text-sm text-red-600">{submissionError}</p>}
            </form>
          </div>

          {/* --- NEW TABULAR JOB TRACKER --- */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
            <DataTable columns={columns} data={trackedJobs} />
          </div>

          {/* ... Existing Watchlist & Job Matches sections ... */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-1">
              <div className="bg-white p-6 rounded-lg shadow-md">
                  <h2 className="text-2xl font-semibold text-gray-800 mb-4">Watchlist</h2>
                  <p className="text-gray-500">Watchlist feature coming soon.</p>
              </div>
            </div>
            <div className="md:col-span-2">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4">Job Matches</h2>
                <ul className="space-y-4">
                  {jobs.length > 0 ? (
                    jobs.map((job) => (
                      <li key={job.id} className="border-b pb-4 flex justify-between items-center">
                        <div>
                          <h3 className="font-bold text-lg text-blue-600">{job.job_title}</h3>
                          <p className="text-gray-700">{job.company_name}</p>
                          <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline">View Job</a>
                        </div>
                        <button onClick={() => handleTrackJob(job.id)} className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-300">
                          Track
                        </button>
                      </li>
                    ))
                  ) : ( <li className="text-gray-500">No jobs found yet.</li> )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <h2 className="text-xl font-semibold">Data not available</h2>
          <p className="text-gray-600">There was an issue loading your dashboard data. Please try refreshing the page.</p>
          {debugError && <p className="text-sm mt-2 text-red-700"><strong>Error Details:</strong> {debugError}</p>}
        </div>
      )}
    </main>
  );
}