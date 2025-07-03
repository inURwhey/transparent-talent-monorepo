// Path: apps/frontend/app/dashboard/components/JobTracker.tsx
'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { PaginationState } from '@tanstack/react-table';

// Removed: import { useTrackedJobsApi } from '../hooks/useTrackedJobsApi'; // No longer fetching internally
import { DataTable } from '../data-table';
import { getColumns } from './columns';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { type UpdatePayload, type TrackedJob, type CompanyProfile } from '../types';

interface JobTrackerProps {
    trackedJobs: TrackedJob[]; // Added prop for data
    isLoading: boolean; // Added prop for loading state
    error: string | null; // Added prop for error state
    totalCount: number; // Added prop for total count (for pagination)
    handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
    // Pass necessary actions from useTrackedJobsApi down
    actions: {
        updateTrackedJob: (trackedJobId: number, payload: UpdatePayload) => Promise<void>;
        removeTrackedJob: (trackedJobId: number) => Promise<void>;
        fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
    };
}

const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export default function JobTracker({
    trackedJobs, // Destructure from props
    isLoading,   // Destructure from props
    error,       // Destructure from props
    totalCount,  // Destructure from props
    handleUpdateJobField,
    actions // Destructure actions from props
}: JobTrackerProps) {
    
    const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
    const [filterStatus, setFilterStatus] = useState<'all' | 'active_pipeline' | 'closed_pipeline' | 'active_posting' | 'expired_posting'>('all');

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
        await actions.updateTrackedJob(trackedJobId, payload); // Use actions from props
    }, [actions, trackedJobs]);

    const handleToggleExcited = useCallback(async (trackedJobId: number, isExcited: boolean) => {
        await actions.updateTrackedJob(trackedJobId, { is_excited: isExcited }); // Use actions from props
    }, [actions]);

    const handleRemoveJob = useCallback(async (trackedJobId: number) => {
        if (window.confirm("Are you sure?")) await actions.removeTrackedJob(trackedJobId); // Use actions from props
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
    }, [trackedJobs, filterStatus]); // Use trackedJobs prop here

    useEffect(() => { setPagination(prev => ({ ...prev, pageIndex: 0 })); }, [filterStatus]);

    const columns = useMemo(
        () => getColumns({
            handleStatusChange,
            handleRemoveJob,
            handleToggleExcited,
            handleUpdateJobField,
            allTableData: filteredTrackedJobs,
        }),
        [handleStatusChange, handleRemoveJob, handleToggleExcited, handleUpdateJobField, filteredTrackedJobs]
    );
    
    if (isLoading) { // Use isLoading prop
        return <div className="text-center p-8">Loading your tracked jobs...</div>;
    }

    if (error) { // Use error prop
        return <div className="text-center p-8 text-red-600">Error loading jobs: {error}</div>;
    }

    return (
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
            <DataTable
                columns={columns}
                data={filteredTrackedJobs}
                pagination={pagination}
                setPagination={setPagination}
                totalCount={totalCount} // Use totalCount prop
                fetchCompanyProfile={actions.fetchCompanyProfile} // Use actions from props
            />
        </div>
    );
}