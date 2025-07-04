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
  const { trackedJobs, totalCount, isLoading: isLoadingTrackedJobs, error: trackedJobsError, actions: trackedJobsActions } = useTrackedJobsApi();
  
  const { isLoaded: isUserLoaded, user } = useUser();
  const { getToken } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [profile, setProfile] = useState<Profile | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const handleUpdateJobField = useCallback(async (trackedJobId: number, field: keyof UpdatePayload, value: any) => {
    try {
      await trackedJobsActions.updateTrackedJob(trackedJobId, { [field]: value } as UpdatePayload);
    } catch (error) {
        console.error(`Error updating job field ${String(field)}:`, error);
    }
  }, [trackedJobsActions]);

  const handleJobSubmit = useCallback(async (jobUrl: string) => {
    setIsSubmitting(true);
    setSubmissionError(null);
    try {
        await trackedJobsActions.submitNewJob(jobUrl);
        refetchRecommendations();
    } catch (error) {
        setSubmissionError(error instanceof Error ? error.message : 'An unknown submission error occurred.');
    } finally {
        setIsSubmitting(false);
    }
  }, [trackedJobsActions, refetchRecommendations]);

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
  
  const dashboardError = recsError || trackedJobsError;
  if (dashboardError) return <div className="min-h-screen flex items-center justify-center text-red-600">Error loading dashboard: {String(dashboardError)}</div>;

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
          jobs={recommendedJobs || []}
          isLoading={isLoadingRecs} 
          error={recsError ? String(recsError) : null}
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
          trackedJobs={trackedJobs}
          totalCount={totalCount}
          isLoading={isLoadingTrackedJobs}
          error={trackedJobsError ? String(trackedJobsError) : null}
          handleUpdateJobField={handleUpdateJobField}
          actions={trackedJobsActions} 
        />
        
      </div>
    </main>
  );
}