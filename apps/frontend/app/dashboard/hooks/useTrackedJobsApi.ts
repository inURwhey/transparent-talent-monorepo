// Path: apps/frontend/app/dashboard/hooks/useTrackedJobsApi.ts
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type TrackedJob, type UpdatePayload } from '../types';

export function useTrackedJobsApi() {
  const { getToken, isLoaded: isUserLoaded } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();
    if (!token) throw new Error("Authentication token is missing.");
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('Content-Type', 'application/json');
    return fetch(url, { ...options, headers });
  }, [getToken]);

  useEffect(() => {
    if (isUserLoaded) {
      setIsLoading(true);
      authedFetch(`${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`)
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            setTrackedJobs(data.tracked_jobs);
        })
        .catch(err => setError(err.message))
        .finally(() => setIsLoading(false));
    }
  }, [isUserLoaded, apiBaseUrl, authedFetch]);

  const submitNewJob = useCallback(async (jobUrl: string): Promise<TrackedJob> => {
    const response = await authedFetch(`${apiBaseUrl}/api/jobs/submit`, {
      method: 'POST', body: JSON.stringify({ job_url: jobUrl }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to submit job.');
    setTrackedJobs(prev => [result, ...prev]);
    return result;
  }, [apiBaseUrl, authedFetch]);

  const updateTrackedJob = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    setTrackedJobs(prev => prev.map(job => job.tracked_job_id === trackedJobId ? { ...job, ...payload } : job));
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
        method: 'PUT', body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error("Update failed, will revert.");
      const updatedFromServer = await response.json();
      setTrackedJobs(prev => prev.map(job => job.tracked_job_id === trackedJobId ? updatedFromServer : job));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
      // Revert logic: This requires fetching all jobs again to ensure consistency
      authedFetch(`${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`).then(res => res.json()).then(data => setTrackedJobs(data.tracked_jobs));
    }
  }, [apiBaseUrl, authedFetch]);

  const removeTrackedJob = useCallback(async (trackedJobId: number) => {
    const originalJobs = trackedJobs;
    setTrackedJobs(prev => prev.filter(job => job.tracked_job_id !== trackedJobId));
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
      if (!response.ok) setTrackedJobs(originalJobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
      setTrackedJobs(originalJobs);
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]); // trackedJobs is needed here for the revert action

  return { trackedJobs, isLoading, error, actions: { submitNewJob, updateTrackedJob, removeTrackedJob }};
}