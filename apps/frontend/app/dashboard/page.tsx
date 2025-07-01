// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { PaginationState } from '@tanstack/react-table';
import Link from 'next/link';

import { useTrackedJobsApi } from './hooks/useTrackedJobsApi';
import { useJobRecommendationsApi } from '../../hooks/useJobRecommendationsApi';
import { DataTable } from './data-table';
import { getColumns } from './components/columns';
import { JobSubmissionForm } from './components/JobSubmissionForm';
import JobsForYou from './components/JobsForYou';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { type UpdatePayload, type Profile, type RecommendedJob } from './types'; // Import RecommendedJob

const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export default function UserDashboard() {
  const router = useRouter();
  const { trackedJobs, isLoading: isLoadingJobs, error: jobsError, actions } = useTrackedJobsApi();
  const { data: recommendedJobs, isLoading: isLoadingRecs, error: recsError, refetch: refetchRecommendations } = useJobRecommendationsApi();
  const { isLoaded: isUserLoaded, user } = useUser();
  const { getToken } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [profile, setProfile] = useState<Profile | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
  const [filterStatus, setFilterStatus] = useState<'all' | 'active_pipeline' | 'closed_pipeline' | 'active_posting' | 'expired_posting'>('all');

  // This hook is now split to avoid re-triggering redirects on every profile state change
  useEffect(() => {
    const fetchInitialProfile = async () => {
      if (!isUserLoaded || profile) return; // Only run once on initial load
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

  // This hook handles the redirect logic separately
  useEffect(() => {
    if (profile && !profile.has_completed_onboarding) {
        router.push('/dashboard/profile');
    }
  }, [profile, router]);


  const handleJobSubmit = useCallback(async (jobUrl: string) => {
    setIsSubmitting(true);
    setSubmissionError(null);
    try {
      await actions.submitNewJob(jobUrl);
      setFilterStatus('all');
      setPagination({ pageIndex: 0, pageSize: 10 });
      await refetchRecommendations(); // <-- This refetches recommendations after tracking a job
    } catch (error) { setSubmissionError(error instanceof Error ? error.message : 'An unknown submission error occurred.'); } 
    finally { setIsSubmitting(false); }
  }, [actions, refetchRecommendations]); // <-- Added refetch to dependency array

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    const currentJob = trackedJobs.find(job => job.tracked_job_id === trackedJobId);
    if (!currentJob) return;
    const payload: UpdatePayload = { status: newStatus };
    const now = new Date().toISOString();
    if (newStatus === 'APPLIED' && !currentJob.applied_at) payload.applied_at = now;
    if (newStatus === 'INTERVIEWING' && !currentJob.first_interview_at) payload.first_interview_at = now;
    if (newStatus === 'OFFER_NEGOTIATIONS' && !currentJob.offer_received_at) payload.offer_received_at = now;
    if (!ACTIVE_PIPELINE_STATUSES.includes(newStatus) && !currentJob.resolved_at) payload.resolved_at = now;
    if (ACTIVE_PIPELINE_STATUSES.includes(newStatus) && currentJob.resolved_at) payload.resolved_at = null;
    await actions.updateTrackedJob(trackedJobId, payload);
  }, [actions, trackedJobs]);

  const handleToggleExcited = useCallback(async (trackedJobId: number, isExcited: boolean) => {
    await actions.updateTrackedJob(trackedJobId, { is_excited: isExcited });
  }, [actions]);

  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (window.confirm("Are you sure?")) await actions.removeTrackedJob(trackedJobId);
  }, [actions]);

  const filteredTrackedJobs = useMemo(() => {
    if (filterStatus === 'all') return trackedJobs;
    return trackedJobs.filter(job => {
      switch (filterStatus) {
        case 'active_pipeline': return ACTIVE_PIPELINE_STATUSES.includes(job.status);
        case 'closed_pipeline': return !ACTIVE_PIPELINE_STATUSES.includes(job.status);
        case 'active_posting': return job.job_posting_status === 'Active';
        case 'expired_posting': return job.job_posting_status !== 'Active';
        default: return true;
      }
    });
  }, [trackedJobs, filterStatus]);

  useEffect(() => { setPagination(prev => ({ ...prev, pageIndex: 0 })); }, [filterStatus]);

  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]);

  const isLoading = !isUserLoaded || isLoadingJobs || !profile;
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  if (jobsError) return <div className="min-h-screen flex items-center justify-center text-center"><div><h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2><p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p><p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md"><strong>Error Details:</strong> {jobsError}</p></div></div>;
  
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
          isProfileComplete={profile.has_completed_onboarding}
        />

        <JobSubmissionForm onSubmit={handleJobSubmit} isSubmitting={isSubmitting} submissionError={submissionError} />
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
          <div className="mb-4">
              <Label htmlFor="filterStatus">Filter by Status:</Label>
              <Select value={filterStatus} onValueChange={(value: any) => setFilterStatus(value)}>
                  <SelectTrigger className="w-[220px]"><SelectValue placeholder="All Jobs"/></SelectTrigger>
                  <SelectContent>
                      <SelectItem value="all">All Jobs</SelectItem>
                      <SelectItem value="active_pipeline">Active Pipeline</SelectItem>
                      <SelectItem value="closed_pipeline">Closed Pipeline</SelectItem>
                      <SelectItem value="active_posting">Active Job Postings</SelectItem>
                      <SelectItem value="expired_posting">Expired Job Postings</SelectItem>
                  </SelectContent>
              </Select>
          </div>
          <DataTable columns={columns} data={filteredTrackedJobs} pagination={pagination} setPagination={setPagination} totalCount={filteredTrackedJobs.length} />
        </div>
      </div>
    </main>
  );
}