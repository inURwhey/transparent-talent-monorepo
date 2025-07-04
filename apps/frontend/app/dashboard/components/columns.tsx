// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import { ColumnDef } from "@tanstack/react-table"
// CORRECTED: Added ChevronRight to the import list
import { ArrowUpDown, MoreHorizontal, Calendar as CalendarIcon, Trash2, ChevronRight } from "lucide-react"
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
import { Textarea } from "@/components/ui/textarea"
import React from "react";
import { type TrackedJob, type UpdatePayload } from '../types';

interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
  handleToggleExcited: (trackedJobId: number, isExcited: boolean) => void;
  handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
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
}: GetColumnsProps): ColumnDef<TrackedJob>[] => [
  {
    id: "select",
    header: ({ table }) => (<Checkbox checked={table.getIsAllPageRowsSelected()} onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)} />),
    cell: ({ row }) => (<Checkbox checked={row.getIsSelected()} onCheckedChange={(value) => row.toggleSelected(!!value)} />),
  },
  {
    id: "expander",
    header: () => null,
    cell: ({ row }) => (
      <Button variant="ghost" size="sm" onClick={() => row.toggleExpanded()}>
        <ChevronRight className={`h-4 w-4 transition-transform ${row.getIsExpanded() ? 'rotate-90' : ''}`} />
      </Button>
    ),
  },
  {
    accessorKey: "job.job_title", 
    header: "Job",
    cell: ({ row }) => (<div className="font-medium">{row.original.job?.job_title}<div className="text-sm text-muted-foreground">{row.original.company?.name}</div></div>),
  },
  {
    accessorKey: "ai_grade",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>AI Grade<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => row.original.ai_grade ? <div className="text-center font-medium">{row.original.ai_grade}</div> : <div className="text-gray-400 italic">N/A</div>,
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
          onValueChange={(newValue) => handleStatusChange(row.original.id, newValue)}
        >
          <SelectTrigger id={`status-select-${row.original.id}`} className="w-auto bg-gray-50">
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
    accessorKey: "is_excited",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Excited?<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => (
        <Checkbox
          checked={row.original.is_excited}
          onCheckedChange={(checked: boolean) => handleToggleExcited(row.original.id, checked)}
        />
    ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date Saved<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => (new Date(row.original.created_at).toLocaleDateString()),
  },
  {
    accessorKey: "next_action_notes",
    header: "Next Action",
    cell: ({ row }) => (
      <Textarea
        defaultValue={row.original.next_action_notes ?? ""}
        onBlur={(e) => handleUpdateJobField(row.original.id, 'next_action_notes', e.target.value)}
        placeholder="Next action..."
      />
    ),
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
            <DropdownMenuItem onClick={() => window.open(job.job_opportunity.url, '_blank')}>View Post</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600" onClick={() => handleRemoveJob(job.id)}>
              <Trash2 className="mr-2 h-4 w-4" /> Remove
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
];