// Path: apps/frontend/app/dashboard/page.tsx
'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { PaginationState } from '@tanstack/react-table';
import Link from 'next/link';

// --- HOOKS, COMPONENTS & UTILITY IMPORTS ---
import { useTrackedJobsApi } from './hooks/useTrackedJobsApi';
import { DataTable } from './data-table';
import { getColumns } from './components/columns';
import { JobSubmissionForm } from './components/JobSubmissionForm';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

// --- TYPE DEFINITIONS ---
import { type UpdatePayload } from './types';


export default function UserDashboard() {
  // --- STATE MANAGEMENT ---
  // All tracked jobs data and actions are now managed by our custom hook.
  const { trackedJobs, isLoading: isLoadingJobs, error: jobsError, actions } = useTrackedJobsApi();

  // The user object from Clerk for display purposes.
  const { isLoaded: isUserLoaded, user } = useUser();

  // Local UI state that remains in the component.
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
  const [filterStatus, setFilterStatus] = useState<'all' | 'active_application' | 'expired_application' | 'active_posting' | 'expired_posting'>('all');

  
  // --- HANDLER FUNCTIONS ---
  // These are now simple wrappers that call the more complex logic from our hook.
  const handleJobSubmit = useCallback(async (jobUrl: string) => {
    setIsSubmitting(true);
    setSubmissionError(null);
    try {
      await actions.submitNewJob(jobUrl);
      setFilterStatus('all');
      setPagination({ pageIndex: 0, pageSize: 10 });
    } catch (error) {
      setSubmissionError(error instanceof Error ? error.message : 'An unknown submission error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  }, [actions]);

  const handleStatusChange = useCallback(async (trackedJobId: number, newStatus: string) => {
    const currentJob = trackedJobs.find(job => job.tracked_job_id === trackedJobId);
    if (!currentJob) return;

    const payload: UpdatePayload = { status: newStatus };
    if (newStatus === "Applied" && !currentJob.applied_at) {
      payload.applied_at = new Date().toISOString();
    } else if (newStatus !== "Applied" && currentJob.status === "Applied") {
      payload.applied_at = null;
    }
    await actions.updateTrackedJob(trackedJobId, payload);
  }, [actions, trackedJobs]);

  const handleToggleExcited = useCallback(async (trackedJobId: number, isExcited: boolean) => {
    await actions.updateTrackedJob(trackedJobId, { is_excited: isExcited });
  }, [actions]);

  const handleRemoveJob = useCallback(async (trackedJobId: number) => {
    if (window.confirm("Are you sure?")) {
      await actions.removeTrackedJob(trackedJobId);
    }
  }, [actions]);


  // --- FILTERING LOGIC ---
  const filteredTrackedJobs = useMemo(() => {
    if (filterStatus === 'all') return trackedJobs;
    return trackedJobs.filter(job => {
      switch (filterStatus) {
        case 'active_application': return ['Applied', 'Interviewing', 'Offer'].includes(job.status);
        case 'expired_application': return ['Expired', 'Rejected', 'Withdrawn', 'Accepted'].includes(job.status);
        case 'active_posting': return job.job_posting_status === 'Active';
        case 'expired_posting': return job.job_posting_status !== 'Active';
        default: return true;
      }
    });
  }, [trackedJobs, filterStatus]);

  useEffect(() => {
    setPagination(prev => ({ ...prev, pageIndex: 0 }));
  }, [filterStatus]);


  // --- COLUMN DEFINITIONS ---
  const columns = useMemo(() => getColumns({ handleStatusChange, handleRemoveJob, handleToggleExcited }), [handleStatusChange, handleRemoveJob, handleToggleExcited]);


  // --- RENDER LOGIC ---
  const isLoading = !isUserLoaded || isLoadingJobs;
  if (isLoading && trackedJobs.length === 0) {
    return <div className="min-h-screen flex items-center justify-center">Loading Dashboard...</div>;
  }
  if (jobsError) {
    return (
      <div className="min-h-screen flex items-center justify-center text-center">
        <div>
          <h2 className="text-xl font-semibold text-red-600">An Error Occurred</h2>
          <p className="text-gray-600 mt-2">There was an issue loading your dashboard data.</p>
          <p className="text-sm mt-4 text-red-700 font-mono bg-red-50 p-4 rounded-md">
            <strong>Error Details:</strong> {jobsError}
          </p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white p-6 rounded-lg shadow-md mb-8 flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{user?.fullName || 'Your Dashboard'}</h1>
              <p className="text-lg text-gray-600 mt-2">Welcome back.</p>
            </div>
            <Link href="/dashboard/profile" passHref>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                Edit Profile
              </Button>
            </Link>
        </div>

        <JobSubmissionForm
          isSubmitting={isSubmitting}
          submissionError={submissionError}
          onSubmit={handleJobSubmit}
        />

        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
          <div className="mb-4">
              <Label htmlFor="filterStatus" className="block text-sm font-medium text-gray-700 mb-1">Filter by Status:</Label>
              <Select value={filterStatus} onValueChange={(value: typeof filterStatus) => setFilterStatus(value)}>
                  <SelectTrigger className="w-[220px]">
                      <SelectValue placeholder="All Jobs" />
                  </SelectTrigger>
                  <SelectContent>
                      <SelectItem value="all">All Jobs</SelectItem>
                      <SelectItem value="active_application">Active Applications</SelectItem>
                      <SelectItem value="expired_application">Expired Applications</SelectItem>
                      <SelectItem value="active_posting">Active Job Postings</SelectItem>
                      <SelectItem value="expired_posting">Expired Job Postings</SelectItem>
                  </SelectContent>
              </Select>
          </div>
          <DataTable
            columns={columns}
            data={filteredTrackedJobs}
            pagination={pagination}
            setPagination={setPagination}
            totalCount={filteredTrackedJobs.length}
          />
        </div>
      </div>
    </main>
  );
}