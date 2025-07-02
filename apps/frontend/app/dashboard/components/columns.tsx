// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import React, { useState, useEffect, useCallback } from 'react';
import { ColumnDef, Row } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, ChevronRight, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import UnlockAIGradeCTA from "./UnlockAIGradeCTA"
import { type TrackedJob, type CompanyProfile } from '../types';

interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
  handleToggleExcited: (trackedJobId: number, isExcited: boolean) => void;
  fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
}

const SUCCESS_STATUSES = ['OFFER_ACCEPTED'];
const NEGATIVE_TERMINAL_STATUSES = ['REJECTED', 'EXPIRED'];
const NEUTRAL_TERMINAL_STATUSES = ['WITHDRAWN'];
const ACTIVE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

const RowSubComponent = ({ row, fetchCompanyProfile }: { row: Row<TrackedJob>, fetchCompanyProfile: GetColumnsProps['fetchCompanyProfile'] }) => {
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadProfile = useCallback(async () => {
    if (!row.original.company_id) return;
    setIsLoading(true);
    const fetchedProfile = await fetchCompanyProfile(row.original.company_id);
    setProfile(fetchedProfile);
    setIsLoading(false);
  }, [fetchCompanyProfile, row.original.company_id]);

  useEffect(() => {
    if(row.getIsExpanded()) {
        loadProfile();
    }
  }, [row.getIsExpanded(), loadProfile]);

  return (
    <div className="p-4 bg-gray-50/50 border-l-4 border-blue-500">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Company Snapshot</h3>
        {isLoading && (
            <div className="flex items-center text-gray-500">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                <span>Loading company profile...</span>
            </div>
        )}
        {!isLoading && !profile && (
            <p className="text-gray-500 text-sm">No company profile has been generated yet.</p>
        )}
        {!isLoading && profile && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                    <p className="font-semibold text-gray-600">Industry</p>
                    <p className="text-gray-800">{profile.industry || 'N/A'}</p>
                </div>
                <div className="space-y-1">
                    <p className="font-semibold text-gray-600">Employee Count</p>
                    <p className="text-gray-800">{profile.employee_count_range || 'N/A'}</p>
                </div>
                <div className="space-y-1 col-span-1 md:col-span-2">
                    <p className="font-semibold text-gray-600">Business Model</p>
                    <p className="text-gray-800">{profile.primary_business_model || 'N/A'}</p>
                </div>
                <div className="space-y-1 col-span-1 md:col-span-2">
                    <p className="font-semibold text-gray-600">Stated Mission</p>
                    <p className="text-gray-800 italic">"{profile.publicly_stated_mission || 'N/A'}"</p>
                </div>
            </div>
        )}
    </div>
  );
};

export const getColumns = ({ handleStatusChange, handleRemoveJob, handleToggleExcited, fetchCompanyProfile }: GetColumnsProps): ColumnDef<TrackedJob>[] => [
  {
    id: "expander",
    header: () => null,
    cell: ({ row }) => (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => row.toggleExpanded()}
        disabled={!row.getCanExpand()}
      >
        <ChevronRight className={`h-4 w-4 transition-transform ${row.getIsExpanded() ? 'rotate-90' : ''}`} />
      </Button>
    ),
  },
  {
    id: "select",
    header: ({ table }) => (<Checkbox checked={table.getIsAllPageRowsSelected()} onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)} />),
    cell: ({ row }) => (<Checkbox checked={row.getIsSelected()} onCheckedChange={(value) => row.toggleSelected(!!value)} />),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "job_title",
    header: "Job",
    cell: ({ row }) => (<div className="font-medium">{row.original.job_title}<div className="text-sm text-muted-foreground">{row.original.company_name}</div></div>),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.original.status;
      let textColor = "text-gray-700";
      if (SUCCESS_STATUSES.includes(status)) { textColor = "text-green-600 font-semibold"; }
      else if (NEGATIVE_TERMINAL_STATUSES.includes(status)) { textColor = "text-red-600 font-semibold"; }
      else if (NEUTRAL_TERMINAL_STATUSES.includes(status)) { textColor = "text-gray-600"; }
      else if (ACTIVE_STATUSES.includes(status)) { textColor = "text-blue-600"; }
      return (
        <Select
          value={status}
          onValueChange={(newValue) => handleStatusChange(row.original.tracked_job_id, newValue)}
        >
          <SelectTrigger className="w-[180px] bg-gray-50">
            <SelectValue className={textColor} placeholder="Select Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="SAVED" className={ACTIVE_STATUSES.includes('SAVED') ? "text-blue-600" : ""}>Saved</SelectItem>
            <SelectItem value="APPLIED" className={ACTIVE_STATUSES.includes('APPLIED') ? "text-blue-600" : ""}>Applied</SelectItem>
            <SelectItem value="INTERVIEWING" className={ACTIVE_STATUSES.includes('INTERVIEWING') ? "text-blue-600" : ""}>Interviewing</SelectItem>
            <SelectItem value="OFFER_NEGOTIATIONS" className={ACTIVE_STATUSES.includes('OFFER_NEGOTIATIONS') ? "text-blue-600" : ""}>Offer</SelectItem>
            <SelectItem value="REJECTED" className={NEGATIVE_TERMINAL_STATUSES.includes('REJECTED') ? "text-red-600" : ""}>Rejected</SelectItem>
            <SelectItem value="EXPIRED" className={NEGATIVE_TERMINAL_STATUSES.includes('EXPIRED') ? "text-red-600" : ""}>Expired</SelectItem>
            <SelectItem value="WITHDRAWN" className={NEUTRAL_TERMINAL_STATUSES.includes('WITHDRAWN') ? "text-gray-600" : ""}>Withdrawn</SelectItem>
            <SelectItem value="OFFER_ACCEPTED" className={SUCCESS_STATUSES.includes('OFFER_ACCEPTED') ? "text-green-600" : ""}>Accepted</SelectItem>
          </SelectContent>
        </Select>
      );
    },
  },
  {
    accessorKey: "status_reason",
    header: "Status Reason",
    cell: ({ row }) => (<div className="text-sm text-muted-foreground">{row.original.status_reason || "-"}</div>),
  },
  {
    accessorKey: "job_posting_status",
    header: "Job Post Status",
    cell: ({ row }) => {
      const status = row.original.job_posting_status;
      const lastChecked = row.original.last_checked_at;
      const formattedDate = lastChecked ? new Date(lastChecked).toLocaleDateString() : 'N/A';
      let textColor = "text-gray-700";
      if (status === "Active") { textColor = "text-green-600"; }
      else if (status && status.includes("Expired")) { textColor = "text-red-600"; }
      return (
        <div className={`font-medium ${textColor}`}>
          {status || "Unknown"}
          {lastChecked && <div className="text-xs text-muted-foreground mt-0.5">Checked: {formattedDate}</div>}
        </div>
      );
    },
  },
  {
    accessorKey: "ai_grade",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>AI Grade<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const analysis = row.original.ai_analysis;
      if (!analysis || !analysis.matrix_rating) { return <UnlockAIGradeCTA />; }
      return <div className="text-center font-medium">{analysis.matrix_rating}</div>
    },
    sortingFn: (rowA, rowB) => {
      const gradeA = rowA.original.ai_analysis?.matrix_rating || 'Z';
      const gradeB = rowB.original.ai_analysis?.matrix_rating || 'Z';
      return gradeA.localeCompare(gradeB);
    }
  },
  {
    accessorKey: "is_excited",
    header: "Excited?",
    cell: ({ row }) => (<div className="flex items-center justify-center"> <Checkbox checked={row.original.is_excited} onCheckedChange={(checked: boolean) => { handleToggleExcited(row.original.tracked_job_id, checked); }} /> </div>),
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date Saved<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => (new Date(row.original.created_at).toLocaleDateString())
  },
  {
    accessorKey: "applied_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date Applied<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const appliedAt = row.original.applied_at;
      if (!appliedAt) { return <div className="text-center">-</div>; }
      return new Date(appliedAt).toLocaleDateString();
    }
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const job = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild><Button variant="ghost" className="h-8 w-8 p-0"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => navigator.clipboard.writeText(job.job_title)}>Copy Title</DropdownMenuItem>
            <DropdownMenuItem onClick={() => window.open(job.job_url, '_blank')}>View Post</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600" onClick={() => handleRemoveJob(job.tracked_job_id)}>Remove</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
];

export { RowSubComponent };