// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import Link from 'next/link';

import { useJobRecommendationsApi } from '../../hooks/useJobRecommendationsApi';
import { useTrackedJobsApi } from './hooks/useTrackedJobsApi';

import { JobSubmissionForm } from './components/JobSubmissionForm';
import JobsForYou from './components/JobsForYou';
import JobTracker from './components/JobTracker';
import { Button } from '@/components/ui/button';
import { type Profile, type UpdatePayload } from './types';

export default function UserDashboard() {
  const { data: recommendedJobs, isLoading: isLoadingRecs, error: recsError, refetch: refetchRecommendations } = useJobRecommendationsApi();
  const { trackedJobs: trackedJobsData, isLoading: isLoadingTrackedJobs, error: trackedJobsError, refetch: refetchTrackedJobs, actions: trackedJobsActions } = useTrackedJobsApi();
  
  const { isLoaded: isUserLoaded, user } = useUser();
  const { getToken } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [profile, setProfile] = useState<Profile | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const handleUpdateJobField = useCallback(async (trackedJobId: number, field: keyof UpdatePayload, value: any) => {
    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication token is missing.");

      const payload: UpdatePayload = {
        [field]: value
      };

      // The useTrackedJobsApi.updateTrackedJob already handles optimistic updates and re-syncs.
      // Calling refetchTrackedJobs() here is redundant and causes an unnecessary full table re-render.
      // We will now call the action directly and let it manage the state update.
      await trackedJobsActions.updateTrackedJob(trackedJobId, payload); 

    } catch (error) {
        console.error(`Error updating job field ${String(field)}:`, error);
        // If update fails, the useTrackedJobsApi hook itself will refetch, reverting optimistic update
    }
  }, [getToken, apiBaseUrl, trackedJobsActions]); // Depend on trackedJobsActions instead of refetchTrackedJobs

  const handleJobSubmit = useCallback(async (jobUrl: string) => {
    setIsSubmitting(true);
    setSubmissionError(null);
    try {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");

        const response = await fetch(`${apiBaseUrl}/api/jobs/submit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ job_url: jobUrl })
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Failed to submit job.');
        
        // Keep these refetches. New job submission implies a change that affects
        // both tracked jobs list and recommendations (if relevant).
        refetchTrackedJobs();
        refetchRecommendations();

    } catch (error) {
        setSubmissionError(error instanceof Error ? error.message : 'An unknown submission error occurred.');
    } finally {
        setIsSubmitting(false);
    }
  }, [getToken, apiBaseUrl, refetchTrackedJobs, refetchRecommendations]);

  useEffect(() => {
    const fetchInitialProfile = async () => {
        if (!isUserLoaded || profile) return;
        try {
            const token = await getToken();
            if (!token) return;
            const response = await fetch(`${apiBaseUrl}/api/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error("Could not fetch profile");
            const profileData: Profile = await response.json();
            setProfile(profileData);
        } catch (error) { console.error("Failed to fetch initial profile:", error); }
    };
    fetchInitialProfile();
  }, [isUserLoaded, getToken, apiBaseUrl, profile]);

  const isLoading = !isUserLoaded || !profile || isLoadingRecs || isLoadingTrackedJobs;
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  
  if (recsError) return <div className="min-h-screen flex items-center justify-center text-red-600">Error loading recommendations: {recsError}</div>;
  if (trackedJobsError) return <div className="min-h-screen flex items-center justify-center text-red-600">Error loading tracked jobs: {trackedJobsError}</div>;

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="bg-white p-6 rounded-lg shadow-md flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{user?.fullName || 'Your Dashboard'}</h1>
              <p className="text-lg text-gray-600 mt-2">Welcome back.</p>
            </div>
            <Link href="/dashboard/profile" passHref><Button>Edit Profile</Button></Link>
        </div>

        <JobsForYou 
          jobs={recommendedJobs} 
          isLoading={isLoadingRecs} 
          error={recsError} 
          onTrack={handleJobSubmit}
          isSubmitting={isSubmitting}
          isProfileComplete={profile!.has_completed_onboarding}
        />
        
        <JobSubmissionForm 
          onSubmit={handleJobSubmit}
          isSubmitting={isSubmitting} 
          submissionError={submissionError} 
          isProfileComplete={profile!.has_completed_onboarding}
        />
        
        <JobTracker 
          trackedJobs={trackedJobsData || []}
          totalCount={trackedJobsData?.length || 0}
          isLoading={isLoadingTrackedJobs}
          error={trackedJobsError}
          handleUpdateJobField={handleUpdateJobField}
          actions={trackedJobsActions}
        />
        
      </div>
    </main>
  );
}