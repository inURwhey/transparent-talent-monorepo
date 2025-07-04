// Path: apps/frontend/app/dashboard/hooks/useTrackedJobsApi.ts
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type TrackedJob, type UpdatePayload, type Profile, type CompanyProfile } from '../types'; // Ensure CompanyProfile is imported

export function useTrackedJobsApi() {
  const { getToken, isLoaded: isUserLoaded } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [trackedJobs, setTrackedJobs] = useState<TrackedJob[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
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
    authedFetch(`${apiBaseUrl}/api/tracked-jobs?page=1&limit=1000`)
      .then(async (res) => {
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ error: `Server responded with ${res.status}` }));
          throw new Error(errorData.error || `Server responded with ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
          setTrackedJobs(data.jobs || []);
          setTotalCount(data.total_count || 0);
      })
      .catch(err => {
          console.error("Error fetching tracked jobs:", err); 
          setError(err.message);
          setTrackedJobs([]);
          setTotalCount(0);
      })
      .finally(() => setIsLoading(false));
  }, [isUserLoaded, apiBaseUrl, authedFetch]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const submitNewJob = useCallback(async (jobUrl: string) => {
    await authedFetch(`${apiBaseUrl}/api/jobs/submit`, { method: 'POST', body: JSON.stringify({ job_url: jobUrl }) });
    fetchJobs();
  }, [apiBaseUrl, authedFetch, fetchJobs]);

  const updateTrackedJob = useCallback(async (trackedJobId: number, payload: UpdatePayload) => {
    setTrackedJobs(prev => prev.map(job => (job.id === trackedJobId ? { ...job, ...payload } : job)));
    
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'PUT', body: JSON.stringify(payload) });
      if (!response.ok) throw new Error('Update failed');
      const updatedFromServer = await response.json();
      setTrackedJobs(prev => prev.map(job => (job.id === trackedJobId ? updatedFromServer : job)));
    } catch (err) {
      console.error(`Error during update for job ${trackedJobId}:`, err);
      setError(err instanceof Error ? err.message : "Update failed.");
      fetchJobs();
    }
  }, [apiBaseUrl, authedFetch, fetchJobs]);

  const removeTrackedJob = useCallback(async (trackedJobId: number) => {
    const originalJobs = [...trackedJobs];
    setTrackedJobs(prev => prev.filter(job => job.id !== trackedJobId));
    setTotalCount(prev => prev - 1);
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Delete failed');
    } catch (err) {
      console.error(`Error during remove for job ${trackedJobId}:`, err);
      setError(err instanceof Error ? err.message : "Delete failed.");
      setTrackedJobs(originalJobs);
      setTotalCount(originalJobs.length);
    }
  }, [apiBaseUrl, authedFetch, trackedJobs]);

  const fetchCompanyProfile = useCallback(async (companyId: number): Promise<CompanyProfile | null> => {
    try {
      const response = await authedFetch(`${apiBaseUrl}/api/companies/${companyId}/profile`);
      if (response.status === 404) return null;
      if (!response.ok) throw new Error('Failed to fetch company profile.');
      // The profile might not exist, so we need to handle the JSON parsing carefully
      const text = await response.text();
      return text ? JSON.parse(text) : null;
    } catch (err) {
      console.error("[useTrackedJobsApi] Error fetching company profile:", err);
      return null;
    }
  }, [apiBaseUrl, authedFetch]);


  return {
    trackedJobs,
    totalCount,
    isLoading,
    error,
    refetch: fetchJobs,
    actions: {
      submitNewJob,
      updateTrackedJob,
      removeTrackedJob,
      fetchCompanyProfile // RESTORED
    }
  };
}