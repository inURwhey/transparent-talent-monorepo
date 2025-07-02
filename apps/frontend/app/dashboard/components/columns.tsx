// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, ChevronRight } from "lucide-react"
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
import { type TrackedJob } from '../types';

interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
  handleToggleExcited: (trackedJobId: number, isExcited: boolean) => void;
}

const SUCCESS_STATUSES = ['OFFER_ACCEPTED'];
const NEGATIVE_TERMINAL_STATUSES = ['REJECTED', 'EXPIRED'];
const NEUTRAL_TERMINAL_STATUSES = ['WITHDRAWN'];
const ACTIVE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export const getColumns = ({ handleStatusChange, handleRemoveJob, handleToggleExcited }: GetColumnsProps): ColumnDef<TrackedJob>[] => [
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