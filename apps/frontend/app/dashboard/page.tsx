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


// --- TYPE DEFINITIONS (CORRECTED TO MATCH DB SCHEMA) ---
interface Profile {
  full_name: string;
  short_term_career_goal: string;
}
interface Job { // For job matches from /api/jobs
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
interface TrackedJob { // This now reflects the likely JSON from the /api/tracked-jobs endpoint
  id: number; // The primary key from the tracked_jobs table
  job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  status: string;
  notes: string | null; // Corrected from user_notes
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

  // --- REVISED ISOLATED DATA FETCHING LOGIC ---
  const fetchDataForPage = useCallback(async () => {
    console.log("%cDEBUG: fetchDataForPage triggered.", "color: blue; font-weight: bold;");

    if (!isUserLoaded || !user) {
        console.log("DEBUG: Aborting fetch, user not loaded yet.");
        return;
    }
    
    try {
      console.log("DEBUG: Starting data fetch sequence.");
      setDebugError(null);
      setIsLoading(true);

      if (!apiBaseUrl) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set.");
      
      // --- Fetching sequentially to isolate timeouts ---
      
      console.log("DEBUG: 1. Fetching Profile...");
      const profileRes = await authedFetch(`${apiBaseUrl}/api/profile`);
      if (!profileRes.ok) throw new Error(`Profile fetch failed: ${profileRes.status} ${profileRes.statusText}`);
      const profileData = await profileRes.json();
      console.log("%cDEBUG: 1. Profile fetch SUCCEEDED.", "color: green;", profileData);
      setProfile(profileData);

      console.log("DEBUG: 2. Fetching Jobs...");
      const jobsRes = await authedFetch(`${apiBaseUrl}/api/jobs`);
      if (!jobsRes.ok) throw new Error(`Jobs fetch failed: ${jobsRes.status} ${jobsRes.statusText}`);
      const jobsData = await jobsRes.json();
      console.log("%cDEBUG: 2. Jobs fetch SUCCEEDED.", "color: green;", jobsData);
      setJobs(jobsData);

      console.log("DEBUG: 3. Fetching Tracked Jobs...");
      const trackedJobsRes = await authedFetch(`${apiBaseUrl}/api/tracked-jobs`);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed: ${trackedJobsRes.status} ${trackedJobsRes.statusText}`);
      const trackedJobsData = await trackedJobsRes.json();
      console.log("%cDEBUG: 3. Tracked Jobs fetch SUCCEEDED. Inspect the raw data object below.", "color: green;", trackedJobsData);
      setTrackedJobs(trackedJobsData);
      
      console.log("%cDEBUG: All data fetched and state set successfully.", "color: green; font-weight: bold;");

    } catch (error: unknown) {
      console.error("DEBUG: A critical error was caught in fetchDataForPage:", error);
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred.");
    } finally {
      console.log("DEBUG: 'finally' block reached. Setting isLoading to false.");
      setIsLoading(false);
    }
  }, [apiBaseUrl, isUserLoaded, user, authedFetch]);

  useEffect(() => {
    if (isUserLoaded) {
        fetchDataForPage();
    }
  }, [isUserLoaded, fetchDataForPage]);

  const handleUpdate = useCallback(async (jobId: number, payload: UpdatePayload) => {
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${jobId}`, {
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

  const handleRemoveJob = useCallback(async (jobId: number) => {
    if (!window.confirm("Are you sure?")) return;
    try {
        const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${jobId}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to remove job.');
        setTrackedJobs(currentJobs => currentJobs.filter(job => job.id !== jobId));
    } catch (error) {
        console.error("Remove Job Error:", error);
        alert("Could not remove the job.");
    }
  }, [apiBaseUrl, authedFetch]);

  const handleStatusChange = useCallback(async (jobId: number, newStatus: string) => {
    await handleUpdate(jobId, { status: newStatus });
  }, [handleUpdate]);

  const handleJobSubmit = useCallback(async (event: FormEvent) => {
    // ... no changes here
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting]);

  const handleTrackJob = useCallback(async (jobId: number) => {
    // ... no changes here
  }, [apiBaseUrl, authedFetch, fetchDataForPage]);
  
  // --- COLUMN DEFINITIONS (CORRECTED) ---
  const columns: ColumnDef<TrackedJob>[] = useMemo(() => [
    {
      id: "select",
      header: ({ table }) => (<Checkbox checked={table.getIsAllPageRowsSelected()} onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)} aria-label="Select all"/>),
      cell: ({ row }) => (<Checkbox checked={row.getIsSelected()} onCheckedChange={(value) => row.toggleSelected(!!value)} aria-label="Select row"/>),
      enableSorting: false, enableHiding: false,
    },
    {
      accessorKey: "job_title",
      header: "Job",
      cell: ({ row }) => {
        const job = row.original;
        return (<div className="font-medium">{job.job_title}<div className="text-sm text-muted-foreground">{job.company_name}</div></div>);
      },
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const job = row.original;
        return (
          <select value={job.status} onChange={(e) => handleStatusChange(job.id, e.target.value)} onClick={(e) => e.stopPropagation()}
            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg p-2 h-fit focus:ring-blue-500 focus:border-blue-500">
            <option value="Saved">Saved</option><option value="Applied">Applied</option><option value="Interviewing">Interviewing</option><option value="Offer">Offer</option><option value="Rejected">Rejected</option>
          </select>
        );
      }
    },
    {
      accessorKey: "relevance_score",
      // ... no changes needed here, already defensive
    },
    {
      accessorKey: "applied_at",
      // ... no changes needed here
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const job = row.original
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild><Button variant="ghost" className="h-8 w-8 p-0"><span className="sr-only">Open menu</span><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(job.job_title)}>Copy Title</DropdownMenuItem>
              <DropdownMenuItem onClick={() => window.open(job.job_url, '_blank')}>View Original Post</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600" onClick={() => handleRemoveJob(job.id)}>Remove Job</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ], [handleStatusChange, handleRemoveJob]);

  // --- RENDER LOGIC (no changes) ---
  if (!isUserLoaded) { /* ... */ }
  if (isLoading) { /* ... */ }
  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      {/* ... */}
    </main>
  );
}