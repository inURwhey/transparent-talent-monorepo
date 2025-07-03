// Path: apps/frontend/app/dashboard/components/JobTracker.tsx
'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { PaginationState } from '@tanstack/react-table';

import { useTrackedJobsApi } from '../hooks/useTrackedJobsApi';
import { DataTable } from '../data-table';
import { getColumns } from './columns';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { type UpdatePayload, type TrackedJob } from '../types';

interface JobTrackerProps {
    // Corrected type for handleUpdateJobField to use keyof UpdatePayload
    handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
}

const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export default function JobTracker({ handleUpdateJobField }: JobTrackerProps) {
    const { trackedJobs, isLoading: isLoadingJobs, error: jobsError, actions } = useTrackedJobsApi();
    
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
    
    if (isLoadingJobs) {
        return <div className="text-center p-8">Loading your tracked jobs...</div>;
    }

    if (jobsError) {
        return <div className="text-center p-8 text-red-600">Error loading jobs: {jobsError}</div>;
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
                totalCount={filteredTrackedJobs.length}
                fetchCompanyProfile={actions.fetchCompanyProfile}
            />
        </div>
    );
}