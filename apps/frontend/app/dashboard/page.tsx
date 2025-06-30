// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation'; // Import useRouter for redirection
import { PaginationState } from '@tanstack/react-table';
import Link from 'next/link';

import { useTrackedJobsApi } from './hooks/useTrackedJobsApi';
import { DataTable } from './data-table';
import { getColumns } from './components/columns';
import { JobSubmissionForm } from './components/JobSubmissionForm';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { type UpdatePayload, type Profile } from './types'; // Import Profile type

const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export default function UserDashboard() {
  const router = useRouter();
  const { trackedJobs, isLoading: isLoadingJobs, error: jobsError, actions } = useTrackedJobsApi();
  const { isLoaded: isUserLoaded, user } = useUser();
  const [profile, setProfile] = useState<Profile | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
  const [filterStatus, setFilterStatus] = useState<'all' | 'active_pipeline' | 'closed_pipeline' | 'active_posting' | 'expired_posting'>('all');

  // --- NEW: This useEffect handles the "Onboarding Trap" ---
  useEffect(() => {
      // We need to fetch the profile separately to check the onboarding status
      const checkOnboardingStatus = async () => {
          if (!isUserLoaded) return;
          try {
              // We can re-use the authedFetch from the hook if we expose it, but for now this is fine.
              const token = await (window as any).Clerk.session?.getToken();
              if (!token) return;

              const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/profile`, {
                  headers: { 'Authorization': `Bearer ${token}` }
              });
              if (!response.ok) return;

              const profileData: Profile = await response.json();
              setProfile(profileData);

              if (!profileData.has_completed_onboarding) {
                  router.push('/dashboard/profile');
              }
          } catch (error) {
              console.error("Failed to check onboarding status:", error);
          }
      };

      checkOnboardingStatus();
  }, [isUserLoaded, router]);


  const handleJobSubmit = useCallback(async (jobUrl: string) => { /* ... (no changes) ... */ }, [actions]);
  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => { /* ... (no changes) ... */ }, [actions, trackedJobs]);
  const handleToggleExcited = useCallback(async (trackedJobId: number, isExcited: boolean) => { /* ... (no changes) ... */ }, [actions]);
  const handleRemoveJob = useCallback(async (trackedJobId: number) => { /* ... (no changes) ... */ }, [actions]);

  const filteredTrackedJobs = useMemo(() => { /* ... (no changes) ... */ }, [trackedJobs, filterStatus]);
  useEffect(() => { setPagination(prev => ({ ...prev, pageIndex: 0 })); }, [filterStatus]);

  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]);

  const isLoading = !isUserLoaded || isLoadingJobs || !profile; // Wait for profile check
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  }
  
  // If user is not onboarded, this component will redirect. We can show a loader or nothing.
  // The redirect logic in useEffect will handle the rest.
  if (!profile?.has_completed_onboarding) {
      return <div className="min-h-screen flex items-center justify-center">Redirecting to complete your profile...</div>;
  }

  if (jobsError) { /* ... (error rendering is unchanged) ... */ }

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white p-6 rounded-lg shadow-md mb-8 flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{user?.fullName || 'Your Dashboard'}</h1>
              <p className="text-lg text-gray-600 mt-2">Welcome back.</p>
            </div>
            <Link href="/dashboard/profile" passHref>
              <Button>Edit Profile</Button>
            </Link>
        </div>
        <JobSubmissionForm onSubmit={handleJobSubmit} isSubmitting={isSubmitting} submissionError={submissionError} />
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
          <div className="mb-4">
              <Label htmlFor="filterStatus">Filter by Status:</Label>
              <Select value={filterStatus} onValueChange={(value: any) => setFilterStatus(value)}>
                  <SelectTrigger className="w-[220px]"><SelectValue /></SelectTrigger>
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