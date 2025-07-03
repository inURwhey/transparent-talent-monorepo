// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, ChevronRight, CalendarIcon, XCircle } from "lucide-react" // Added XCircle icon
import { format } from "date-fns"
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

import UnlockAIGradeCTA from "./UnlockAIGradeCTA"
import { type TrackedJob, type UpdatePayload } from '../types';
import React, { useState, useMemo } from "react";

interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
  handleToggleExcited: (trackedJobId: number, isExcited: boolean) => void;
  handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
  allTableData: TrackedJob[];
}

const SUCCESS_STATUSES = ['OFFER_ACCEPTED'];
const NEGATIVE_TERMINAL_STATUSES = ['REJECTED', 'EXPIRED'];
const NEUTRAL_TERMINAL_STATUSES = ['WITHDRAWN'];
const ACTIVE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export const getColumns = ({
  handleStatusChange,
  handleRemoveJob,
  handleToggleExcited,
  handleUpdateJobField,
  allTableData
}: GetColumnsProps): ColumnDef<TrackedJob>[] => [
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
          {/* Added id and name attributes */}
          <SelectTrigger id={`status-select-${row.original.tracked_job_id}`} name={`status-select-${row.original.tracked_job_id}`} className="w-auto bg-gray-50">
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
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Excited?<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const trackedJobId = row.original.tracked_job_id;
      const currentJobData = useMemo(() =>
        allTableData.find(job => job.tracked_job_id === trackedJobId),
        [allTableData, trackedJobId]
      );
      const isExcited = currentJobData?.is_excited || false;

      return (
        <Checkbox
          checked={isExcited}
          onCheckedChange={(checked: boolean) => handleToggleExcited(trackedJobId, checked)}
          aria-label="Toggle excited status"
        />
      );
    },
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
    accessorKey: "next_action_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Next Action Date<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const trackedJobId = row.original.tracked_job_id;
      const currentJobData = useMemo(() =>
        allTableData.find(job => job.tracked_job_id === trackedJobId),
        [allTableData, trackedJobId]
      );
      const nextActionAt = currentJobData?.next_action_at;

      const dateValue = nextActionAt ? new Date(nextActionAt) : undefined;
      const [open, setOpen] = useState(false);

      return (
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant={"outline"}
              className={cn(
                "w-auto justify-start text-left font-normal bg-gray-50",
                !dateValue && "text-muted-foreground"
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateValue ? format(dateValue, "PPP") : <span>Pick a date</span>}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={dateValue}
              onSelect={(date) => {
                handleUpdateJobField(trackedJobId, 'next_action_at', date ? date.toISOString() : null);
                setOpen(false);
              }}
              initialFocus
              fromDate={new Date()} // Prevent setting dates in the past
            />
            {dateValue && (
              <div className="p-2 pt-0">
                <Button 
                  variant="ghost" 
                  onClick={() => {
                    handleUpdateJobField(trackedJobId, 'next_action_at', null); // Clear date
                    setOpen(false);
                  }}
                  className="w-full text-sm text-red-500 hover:text-red-600"
                >
                  <XCircle className="mr-2 h-4 w-4" /> Clear Date
                </Button>
              </div>
            )}
          </PopoverContent>
        </Popover>
      );
    }
  },
  {
    accessorKey: "next_action_notes",
    header: "Next Action Notes",
    cell: ({ row }) => {
      const trackedJobId = row.original.tracked_job_id;
      const currentJobData = useMemo(() =>
        allTableData.find(job => job.tracked_job_id === trackedJobId),
        [allTableData, trackedJobId]
      );
      const notes = currentJobData?.next_action_notes;

      return (
        <Textarea
          id={`next-action-notes-${trackedJobId}`} // Added id attribute
          name={`next-action-notes-${trackedJobId}`} // Added name attribute
          key={trackedJobId + (notes || "")}
          defaultValue={notes || ""}
          placeholder="Add notes..."
          onBlur={(e) => {
            if (e.target.value !== (notes || "")) {
              handleUpdateJobField(trackedJobId, 'next_action_notes', e.target.value || null);
            }
          }}
          className="min-h-[50px] bg-gray-50 text-sm"
        />
      );
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