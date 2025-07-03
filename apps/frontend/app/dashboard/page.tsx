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
  // Corrected destructuring for useTrackedJobsApi - it returns 'trackedJobs' directly, not nested in 'data'.
  // Also destructure 'actions' to pass down to JobTracker.
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

      const response = await fetch(`${apiBaseUrl}/api/tracked-jobs/${trackedJobId}`, {
          method: 'PUT',
          headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Failed to update job field ${String(field)}.`);
      
      // Trigger refetch of tracked jobs to update UI
      refetchTrackedJobs();

    } catch (error) {
        console.error(`Error updating job field ${String(field)}:`, error);
    }
  }, [getToken, apiBaseUrl, refetchTrackedJobs]);

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
        if (!isUserLoaded || profile) return; // Only fetch if user is loaded and profile is not yet set
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

  // Combine loading states for a single dashboard loading indicator
  const isLoading = !isUserLoaded || !profile || isLoadingRecs || isLoadingTrackedJobs;
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  
  // Display errors if any exist for recommendations or tracked jobs
  // Removed .message as error is already a string
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
          trackedJobs={trackedJobsData || []} // Pass the fetched data as a prop
          totalCount={trackedJobsData?.length || 0} // trackedJobsData is an array, so its length is the total count for client-side pagination
          isLoading={isLoadingTrackedJobs} // Pass loading state
          error={trackedJobsError} // Pass error state
          handleUpdateJobField={handleUpdateJobField}
          actions={trackedJobsActions} // Pass the actions object
        />
        
      </div>
    </main>
  );
}