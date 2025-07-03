// Path: apps/frontend/hooks/useTrackedJobsApi.ts
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type TrackedJob, type UpdatePayload, type CompanyProfile } from '../types';

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

  const fetchJobs = useCallback(() => {
    if (!isUserLoaded) return;
    setIsLoading(true);
    setError(null);
    console.log("Fetching tracked jobs..."); // Log fetch attempt
    authedFetch(`${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`)
      .then(async (res) => {
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ error: `Server responded with ${res.status}` }));
          throw new Error(errorData.error || `Server responded with ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
          console.log("Tracked jobs fetched successfully:", data.tracked_jobs); // Log fetched data
          setTrackedJobs(data.tracked_jobs || []);
      })
      .catch(err => {
          console.error("Error fetching tracked jobs:", err); // Log fetch error
          setError(err.message);
          setTrackedJobs([]);
      })
      .finally(() => setIsLoading(false));
  }, [isUserLoaded, apiBaseUrl, authedFetch]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const submitNewJob = useCallback(async (jobUrl: string): Promise<TrackedJob> => {
    const response = await authedFetch(`${apiBaseUrl}/api/jobs/submit`, { method: 'POST', body: JSON.stringify({ job_url: jobUrl }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Failed to submit job.');
    setTrackedJobs(prev => [result, ...prev]);
    return result;
  }, [apiBaseUrl, authedFetch]);

  const updateTrackedJob = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    console.log(`[useTrackedJobsApi] Optimistically updating job ${trackedJobId} with payload:`, payload);
    // Optimistic update: Temporarily update state
    setTrackedJobs(prev => prev.map(job => job.tracked_job_id === trackedJobId ? { ...job, ...payload } : job));
    
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'PUT', body: JSON.stringify(payload) });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `Server responded with ${response.status}` }));
        throw new Error(errorData.error || `Update failed for job ${trackedJobId}.`);
      }
      const updatedFromServer = await response.json();
      console.log(`[useTrackedJobsApi] Update successful for job ${trackedJobId}. Data from server:`, updatedFromServer);
      // Re-set with data from server for final consistency (and to ensure all fields are correctly synced)
      setTrackedJobs(prev => prev.map(job => job.tracked_job_id === trackedJobId ? updatedFromServer : job));
    } catch (err) {
      console.error(`[useTrackedJobsApi] Error during update for job ${trackedJobId}:`, err);
      setError(err instanceof Error ? err.message : "Update failed.");
      fetchJobs(); // Refetch if update fails to ensure consistency (rollback)
    }
  }, [apiBaseUrl, authedFetch, fetchJobs]);

  const removeTrackedJob = useCallback(async (trackedJobId: number) => {
    const originalJobs = [...trackedJobs];
    setTrackedJobs(prev => prev.filter(job => job.tracked_job_id !== trackedJobId));
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
      if (!response.ok) {
        setTrackedJobs(originalJobs); // Revert if delete fails
        const errorData = await response.json().catch(() => ({ error: `Server responded with ${response.status}` }));
        throw new Error(errorData.error || `Delete failed for job ${trackedJobId}.`);
      }
      console.log(`[useTrackedJobsApi] Successfully removed job ${trackedJobId}.`);
    } catch (err) {
      console.error(`[useTrackedJobsApi] Error during remove for job ${trackedJobId}:`, err);
      setError(err instanceof Error ? err.message : "Delete failed.");
      setTrackedJobs(originalJobs); // Revert if delete fails
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]);

  const fetchCompanyProfile = useCallback(async (companyId: number): Promise<CompanyProfile | null> => {
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/companies/${companyId}/profile`);
      if (response.status === 404) {
        console.log(`[useTrackedJobsApi] Company profile not found for ID ${companyId}.`);
        return null;
      }
      if (!response.ok) {
        throw new Error('Failed to fetch company profile.');
      }
      const profileData = await response.json();
      console.log(`[useTrackedJobsApi] Fetched company profile for ID ${companyId}:`, profileData);
      return profileData;
    } catch (err) {
      console.error("[useTrackedJobsApi] Error fetching company profile:", err);
      return null;
    }
  }, [apiBaseUrl, authedFetch]);

  return {
    trackedJobs,
    isLoading,
    error,
    refetch: fetchJobs,
    actions: {
      submitNewJob,
      updateTrackedJob,
      removeTrackedJob,
      fetchCompanyProfile
    }
  };
}