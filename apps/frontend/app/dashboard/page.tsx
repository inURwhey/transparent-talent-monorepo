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

// Define the set of statuses that represent an active application pipeline
const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];


export default function UserDashboard() {
  // --- STATE MANAGEMENT ---
  const { trackedJobs, isLoading: isLoadingJobs, error: jobsError, actions } = useTrackedJobsApi();
  const { isLoaded: isUserLoaded, user } = useUser();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
  const [filterStatus, setFilterStatus] = useState<'all' | 'active_pipeline' | 'closed_pipeline' | 'active_posting' | 'expired_posting'>('all');

  
  // --- HANDLER FUNCTIONS ---
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

    const payload: UpdatePayload = { status: newStatus, updated_at: new Date().toISOString() };
    const now = new Date().toISOString();

    // Implement side effects based on DATA_LIFECYCLE.md
    if (newStatus === 'APPLIED' && !currentJob.applied_at) payload.applied_at = now;
    if (newStatus === 'INTERVIEWING' && !currentJob.first_interview_at) payload.first_interview_at = now;
    if (newStatus === 'OFFER_NEGOTIATIONS' && !currentJob.offer_received_at) payload.offer_received_at = now;
    
    // Set resolved_at for any terminal state
    if (!ACTIVE_PIPELINE_STATUSES.includes(newStatus) && !currentJob.resolved_at) {
        payload.resolved_at = now;
    }
    // Clear resolved_at if moving back to an active state from a terminal one (e.g., accidental click)
    if (ACTIVE_PIPELINE_STATUSES.includes(newStatus) && currentJob.resolved_at) {
        payload.resolved_at = null;
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
        case 'active_pipeline': return ACTIVE_PIPELINE_STATUSES.includes(job.status);
        case 'closed_pipeline': return !ACTIVE_PIPELINE_STATUSES.includes(job.status);
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
                      <SelectItem value="active_pipeline">Active Pipeline</SelectItem>
                      <SelectItem value="closed_pipeline">Closed Pipeline</SelectItem>
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