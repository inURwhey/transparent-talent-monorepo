'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';

// --- UPDATED TYPE DEFINITIONS ---
interface Profile {
  full_name: string;
  short_term_career_goal: string;
}
interface Job {
  id: number; // For job matches from /api/jobs
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
  user_notes: string | null; // Renamed from 'notes'
  applied_at: string | null;
  ai_analysis: AIAnalysis | null; // Added for structured analysis
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
  
  // --- NEW STATE FOR JOB SUBMISSION ---
  const [jobUrl, setJobUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  // --- CLERK HOOKS (Unchanged) ---
  const { getToken } = useAuth();
  const { user, isLoaded: isUserLoaded } = useUser();

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  // --- SECURE, AUTHENTICATED FETCH HELPER (Unchanged) ---
  const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('Content-Type', 'application/json');
    return fetch(url, { ...options, headers });
  }, [getToken]);

  // --- DATA FETCHING LOGIC (Unchanged) ---
  const fetchDataForPage = useCallback(async () => {
    if (!isUserLoaded || !user) {
        return;
    }
    
    try {
      setDebugError(null);
      setIsLoading(true);

      if (!apiBaseaUrl) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set.");
      
      const [profileRes, jobsRes, trackedJobsRes] = await Promise.all([
        authedFetch(`${apiBaseUrl}/api/profile`),
        authedFetch(`${apiBaseUrl}/api/jobs`),
        authedFetch(`${apiBaseUrl}/api/tracked-jobs`)
      ]);

      if (!profileRes.ok) throw new Error(`Profile fetch failed: ${profileRes.statusText || 'No response from server'}`);
      if (!jobsRes.ok) throw new Error(`Jobs fetch failed: ${jobsRes.statusText || 'No response from server'}`);
      if (!trackedJobsRes.ok) throw new Error(`Tracked jobs fetch failed: ${trackedJobsRes.statusText || 'No response from server'}`);

      setProfile(await profileRes.json());
      setJobs(await jobsRes.json());
      setTrackedJobs(await trackedJobsRes.json());

    } catch (error: unknown) {
      console.error("A critical error occurred during data fetching:", error);
      setDebugError(error instanceof Error ? error.message : "An unknown error occurred.");
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, isUserLoaded, user, authedFetch]);

  useEffect(() => {
    fetchDataForPage();
  }, [fetchDataForPage]);


  // --- NEW HANDLER FOR JOB SUBMISSION ---
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
      
      // Add the new job to the top of the list for immediate feedback
      setTrackedJobs(prevJobs => [result, ...prevJobs]);
      setJobUrl(''); // Clear the input on success
    } catch (error: unknown) {
      console.error("Job Submission Error:", error);
      setSubmissionError(error instanceof Error ? error.message : 'An unknown error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  }, [apiBaseUrl, authedFetch, jobUrl, isSubmitting]);

  // --- EXISTING HANDLERS (Unchanged logic, but updated for new types) ---
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

  // --- EDIT HANDLERS & FORMATTERS (Updated for new types) ---
  const handleStartEdit = useCallback((job: TrackedJob) => {
    setEditingJobId(job.tracked_job_id);
    setEditNotes(job.user_notes || ''); // <-- Updated from job.notes
    setEditDate(job.applied_at ? new Date(job.applied_at).toISOString().split('T')[0] : '');
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditingJobId(null); setEditNotes(''); setEditDate('');
  }, []);

  const handleSaveChanges = useCallback(async (trackedJobId: number) => {
    const success = await handleUpdate(trackedJobId, { notes: editNotes, applied_at: editDate || null });
    if (success) handleCancelEdit();
  }, [editDate, editNotes, handleUpdate, handleCancelEdit]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    await handleUpdate(trackedJobId, { status: newStatus });
  }, [handleUpdate]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC'
    });
  }

  // --- RENDER LOGIC ---
  if (!isUserLoaded) {
     return <div className="min-h-screen flex items-center justify-center">Initializing session...</div>
  }
  
  if (isLoading && isUserLoaded) {
     return <div className="min-h-screen flex items-center justify-center">Loading Dashboard Data...</div>
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
       <div className="max-w-4xl mx-auto p-4 mb-4 border-2 border-dashed border-blue-500 bg-blue-50">
        <h2 className="font-bold text-blue-700">Debug Information</h2>
        <p><strong>User Status:</strong> {isUserLoaded && user ? `Loaded (${user.primaryEmailAddress?.emailAddress})` : 'Loading...'}</p>
        <p><strong>API Base URL:</strong> {apiBaseUrl || <span className="font-bold text-red-600">NOT SET</span>}</p>
        {debugError && <p><strong>Caught Error:</strong> <span className="font-bold text-red-600">{debugError}</span></p>}
      </div>
      
      {!debugError && profile ? (
        <div className="max-w-4xl mx-auto">
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

          {/* --- EXISTING JOB TRACKER (Updated to use new data structure) --- */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
            <div className="space-y-6">
              {trackedJobs.length > 0 ? (
                trackedJobs.map((trackedJob) => (
                  <div key={trackedJob.tracked_job_id} className="border-b pb-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-lg text-indigo-600">{trackedJob.job_title}</h3>
                        <p className="text-gray-700">{trackedJob.company_name}</p>
                        <a href={trackedJob.job_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline">
                          View Original Post
                        </a>
                      </div>
                      <select value={trackedJob.status} onChange={(e) => handleStatusChange(trackedJob.tracked_job_id, e.target.value)}
                        className="bg-gray-200 border border-gray-300 text-gray-900 text-sm rounded-lg p-2.5 h-fit">
                        <option value="Saved">Saved</option>
                        <option value="Applied">Applied</option>
                        <option value="Interviewing">Interviewing</option>
                        <option value="Offer">Offer</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                    </div>
                    {/* --- Note: AI Analysis data is available here (trackedJob.ai_analysis) but not yet rendered. --- */}
                    {editingJobId === trackedJob.tracked_job_id ? (
                      <div className="mt-4 space-y-3">
                        <div>
                          <label htmlFor="applied_at" className="block text-sm font-medium text-gray-700">Applied Date</label>
                          <input type="date" id="applied_at" value={editDate} onChange={(e) => setEditDate(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2" />
                        </div>
                        <div>
                          <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
                          <textarea id="notes" rows={3} value={editNotes} onChange={(e) => setEditNotes(e.target.value)}
                            placeholder="e.g., Followed up with hiring manager..."
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2" ></textarea>
                        </div>
                        <div className="flex items-center space-x-2 mt-2">
                          <button onClick={() => handleSaveChanges(trackedJob.tracked_job_id)} className="bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-3 rounded text-sm">Save</button>
                          <button onClick={handleCancelEdit} className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-1 px-3 rounded text-sm">Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-3 text-sm text-gray-600">
                        <p><strong>Applied on:</strong> {formatDate(trackedJob.applied_at)}</p>
                        {/* Updated to use 'user_notes' */}
                        <p className="mt-1"><strong>Notes:</strong> {trackedJob.user_notes || <span className="italic text-gray-400">No notes added.</span>}</p>
                        <div className="flex items-center">
                            <button onClick={() => handleStartEdit(trackedJob)} className="mt-2 text-blue-600 hover:underline text-xs font-semibold">
                                Edit Details
                            </button>
                            <button onClick={() => handleRemoveJob(trackedJob.tracked_job_id)} className="mt-2 ml-4 text-red-600 hover:underline text-xs font-semibold">
                                Remove
                            </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : ( 
                  <p className="text-gray-500">You are not tracking any jobs yet. Submit a job URL above to begin.</p>
              )}
            </div>
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
        </div>
      )}
    </main>
  );
}