// Path: apps/frontend/app/dashboard/hooks/useTrackedJobsApi.ts
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type TrackedJob, type UpdatePayload } from '../types';

export function useTrackedJobsApi() {
  const { getToken, isLoaded: isUserLoaded } = useAuth();

  // Use BACKEND_PREVIEW_URL if available, otherwise default to NEXT_PUBLIC_API_BASE_URL
  const apiBaseUrl = process.env.NEXT_PUBLIC_BACKEND_PREVIEW_URL || process.env.NEXT_PUBLIC_API_BASE_URL;

  // State managed by the hook
  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generic authenticated fetch utility
  const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    if (!token) throw new Error("Authentication token is missing.");
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('Content-Type', 'application/json');
    return fetch(url, { ...options, headers });
  }, [getToken]);

  // Initial fetch for all tracked jobs
  useEffect(() => {
    const fetchInitialJobs = async () => {
      if (!isUserLoaded) return;
      setIsLoading(true);
      try {
        const url = `${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`;
        const response = await authedFetch(url);
        if (!response.ok) throw new Error("Failed to fetch tracked jobs.");
        const data = await response.json();
        setTrackedJobs(data.tracked_jobs);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialJobs();
  }, [isUserLoaded, apiBaseUrl, authedFetch]);


  // Handler to submit a new job
  const submitNewJob = useCallback(async (jobUrl: string): Promise<TrackedJob> => {
    const response = await authedFetch(`${apiBaseUrl}/api/jobs/submit`, {
      method: 'POST',
      body: JSON.stringify({ job_url: jobUrl }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || 'Failed to submit job.');
    }
    setTrackedJobs(prev => [result, ...prev]);
    return result;
  }, [apiBaseUrl, authedFetch]);


  // Handler to update an existing job
  const updateTrackedJob = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    const originalJobs = [...trackedJobs];
    // Optimistic update
    setTrackedJobs(prev => prev.map(job =>
      job.tracked_job_id === trackedJobId ? { ...job, ...payload } : job
    ));

    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error("Update failed, reverting.");

      const updatedFromServer = await response.json();
      // Final update with authoritative data from server
      setTrackedJobs(prev => prev.map(job =>
        job.tracked_job_id === trackedJobId ? updatedFromServer : job
      ));

    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
      setTrackedJobs(originalJobs); // Revert on error
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]);


  // Handler to remove a job
  const removeTrackedJob = useCallback(async (trackedJobId: number) => {
    const originalJobs = [...trackedJobs];
    setTrackedJobs(prev => prev.filter(job => job.tracked_job_id !== trackedJobId));
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error("Delete failed, reverting.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
      setTrackedJobs(originalJobs); // Revert on error
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]);


  // Return all the state and handlers that a component might need
  return {
    trackedJobs,
    isLoading,
    error,
    actions: {
      submitNewJob,
      updateTrackedJob,
      removeTrackedJob,
    },
  };
}