// Path: apps/frontend/app/dashboard/components/JobTracker.tsx
'use client';

import { useState, useMemo, useEffect } from 'react';
import { PaginationState } from '@tanstack/react-table';

import { DataTable } from '../data-table';
import { getColumns } from './columns';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { type UpdatePayload, type TrackedJob, type CompanyProfile } from '../types';

interface JobTrackerProps {
    trackedJobs: TrackedJob[];
    isLoading: boolean;
    error: string | null;
    totalCount: number;
    // This is the generic update function passed from the main page
    handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
    actions: {
        // We only need remove and fetchCompanyProfile from the actions object now
        removeTrackedJob: (trackedJobId: number) => Promise<void>;
        fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
    };
}

const ACTIVE_PIPELINE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export default function JobTracker({
    trackedJobs,
    isLoading,
    error,
    actions,
    handleUpdateJobField, // This is the key prop we will use
}: JobTrackerProps) {
    
    const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: 10 });
    const [filterStatus, setFilterStatus] = useState<'all' | 'active_pipeline' | 'closed_pipeline' | 'active_posting' | 'expired_posting'>('all');

    // This specific handler is no longer needed because handleUpdateJobField is passed directly
    // const handleStatusChange = ...

    // This specific handler is also no longer needed
    // const handleToggleExcited = ...

    const handleRemoveJob = async (trackedJobId: number) => {
        if (window.confirm("Are you sure you want to remove this job from your tracker?")) {
            await actions.removeTrackedJob(trackedJobId);
        }
    };

    const filteredTrackedJobs = useMemo(() => {
        switch (filterStatus) {
            case 'active_pipeline': return trackedJobs.filter(job => ACTIVE_PIPELINE_STATUSES.includes(job.status));
            case 'closed_pipeline': return trackedJobs.filter(job => !ACTIVE_PIPELINE_STATUSES.includes(job.status));
            case 'active_posting': return trackedJobs.filter(job => job.job?.status === 'Active');
            case 'expired_posting': return trackedJobs.filter(job => job.job?.status !== 'Active');
            default: return trackedJobs;
        }
    }, [trackedJobs, filterStatus]);

    useEffect(() => { setPagination(prev => ({ ...prev, pageIndex: 0 })); }, [filterStatus]);

    const paginatedFilteredJobs = useMemo(() => {
        const start = pagination.pageIndex * pagination.pageSize;
        const end = start + pagination.pageSize;
        return filteredTrackedJobs.slice(start, end);
    }, [filteredTrackedJobs, pagination]);

    // CORRECTED: Pass only the props that getColumns actually needs.
    const columns = useMemo(
        () => getColumns({
            handleUpdateJobField,
            handleRemoveJob,
        }),
        [handleUpdateJobField, handleRemoveJob]
    );
    
    if (isLoading) return <div className="text-center p-8">Loading your tracked jobs...</div>;
    if (error) return <div className="text-center p-8 text-red-600">Error loading jobs: {error}</div>;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">My Job Tracker</h2>
            <div className="mb-4">
                <Label htmlFor="filterStatus">Filter by Status:</Label>
                <Select value={filterStatus} onValueChange={(value: any) => setFilterStatus(value)}>
                    <SelectTrigger id="filterStatus" className="w-[220px]"><SelectValue placeholder="All Jobs"/></SelectTrigger>
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
                data={paginatedFilteredJobs}
                pagination={pagination}
                setPagination={setPagination}
                totalCount={filteredTrackedJobs.length}
                fetchCompanyProfile={actions.fetchCompanyProfile}
            />
        </div>
    );
}