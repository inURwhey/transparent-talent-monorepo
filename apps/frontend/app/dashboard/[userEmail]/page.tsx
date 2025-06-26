'use client';

import { useState, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';

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

interface TrackedJob extends Job {
  tracked_job_id: number;
  status: string;
  notes: string | null;
  applied_at: string | null;
}

type UpdatePayload = {
  notes?: string;
  applied_at?: string | null;
  status?: string;
};

export default function UserDashboard() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingJobId, setEditingJobId] = useState<number | null>(null);
  const [editNotes, setEditNotes] = useState('');
  const [editDate, setEditDate] = useState('');

  const pathname = usePathname();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const getEmailFromPath = useCallback(() => {
    const pathParts = pathname.split('/');
    return pathParts[pathParts.length - 1];
  }, [pathname]);

  const fetchDataForPage = useCallback(async () => {
    const userEmail = getEmailFromPath();
    if (userEmail && apiBaseUrl) {
      setIsLoading(true);
      const [profileRes, jobsRes, trackedJobsRes] = await Promise.all([
        fetch(`${apiBaseUrl}/users/${userEmail}/profile`),
        fetch(`${apiBaseUrl}/users/${userEmail}/jobs`),
        fetch(`${apiBaseUrl}/users/${userEmail}/tracked-jobs`)
      ]);

      const profileData = profileRes.ok ? await profileRes.json() : null;
      const jobsData = jobsRes.ok ? await jobsRes.json() : [];
      const trackedJobsData = trackedJobsRes.ok ? await trackedJobsRes.json() : [];

      setProfile(profileData);
      setJobs(jobsData);
      setTrackedJobs(trackedJobsData);
      setIsLoading(false);
    }
  }, [apiBaseUrl, getEmailFromPath]);

  useEffect(() => {
    fetchDataForPage();
  }, [fetchDataForPage]);

  const handleUpdate = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    const userEmail = getEmailFromPath();
    try {
      const response = await fetch(`${apiBaseUrl}/users/${userEmail}/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error('Failed to update.');
      fetchDataForPage(); 
      return true;
    } catch (error) {
      console.error("Update Error:", error);
      alert("Could not update job.");
      return false;
    }
  }, [apiBaseUrl, getEmailFromPath, fetchDataForPage]);

  const handleTrackJob = useCallback(async (jobId: number) => {
    const userEmail = getEmailFromPath();
    try {
      const response = await fetch(`${apiBaseUrl}/users/${userEmail}/tracked-jobs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!response.ok) throw new Error('Failed to track job.');
      alert("Job tracked successfully!");
      fetchDataForPage();
    } catch (error) {
      console.error("Tracking Error:", error);
      alert("Could not track the job. It might already be on your list.");
    }
  }, [apiBaseUrl, getEmailFromPath, fetchDataForPage]);
  
  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (!window.confirm("Are you sure you want to remove this job from your tracker?")) {
        return;
    }
    const userEmail = getEmailFromPath();
    try {
        const response = await fetch(`${apiBaseUrl}/users/${userEmail}/tracked-jobs/${trackedJobId}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to remove job.');
        setTrackedJobs(currentJobs => currentJobs.filter(job => job.tracked_job_id !== trackedJobId));
    } catch (error) {
        console.error("Remove Job Error:", error);
        alert("Could not remove the job.");
    }
  }, [apiBaseUrl, getEmailFromPath]);

  const handleStartEdit = useCallback((job: TrackedJob) => {
    setEditingJobId(job.tracked_job_id);
    setEditNotes(job.notes || '');
    setEditDate(job.applied_at ? new Date(job.applied_at).toISOString().split('T')[0] : '');
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditingJobId(null); setEditNotes(''); setEditDate('');
  }, []);

  const handleSaveChanges = useCallback(async (trackedJobId: number) => {
    const payload = { notes: editNotes, applied_at: editDate || null };
    const success = await handleUpdate(trackedJobId, payload);
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

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h1 className="text-3xl font-bold text-gray-800">{profile ? profile.full_name : 'User Profile'}</h1>
            <p className="text-lg text-gray-600 mt-2">Short Term Goal:</p>
            <p className="text-gray-700 italic">{profile?.short_term_career_goal || "No goal set."}</p>
        </div>
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
                    <select value={trackedJob.status} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleStatusChange(trackedJob.tracked_job_id, e.target.value)}
                      className="bg-gray-200 border border-gray-300 text-gray-900 text-sm rounded-lg p-2.5 h-fit">
                      <option value="Saved">Saved</option>
                      <option value="Applied">Applied</option>
                      <option value="Interviewing">Interviewing</option>
                      <option value="Offer">Offer</option>
                      <option value="Rejected">Rejected</option>
                    </select>
                  </div>
                  {editingJobId === trackedJob.tracked_job_id ? (
                    <div className="mt-4 space-y-3">
                      <div>
                        <label htmlFor="applied_at" className="block text-sm font-medium text-gray-700">Applied Date</label>
                        <input type="date" id="applied_at" value={editDate} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditDate(e.target.value)}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2" />
                      </div>
                      <div>
                        <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
                        <textarea id="notes" rows={3} value={editNotes} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditNotes(e.target.value)}
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
                      <p className="mt-1"><strong>Notes:</strong> {trackedJob.notes || <span className="italic text-gray-400">No notes added.</span>}</p>
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
                <p className="text-gray-500">You are not tracking any jobs yet. Click 'Track' on a job match to begin.</p> 
            )}
          </div>
        </div>
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
    </main>
  );
}