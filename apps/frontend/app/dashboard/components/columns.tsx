// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
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

// --- TYPE DEFINITIONS ---
// Keep types in sync with page.tsx
interface AIAnalysis {
  position_relevance_score: number;
  environment_fit_score: number;
}
interface TrackedJob {
  tracked_job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  status: string;
  applied_at: string | null;
  created_at: string; // The date the job was saved
  ai_analysis: AIAnalysis | null;
}

// --- PROPS FOR THE GETCOLUMNS FUNCTION ---
interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
}

// This function generates the column definitions.
// It takes callbacks as arguments to keep the column logic separate from the page logic.
export const getColumns = ({ handleStatusChange, handleRemoveJob }: GetColumnsProps): ColumnDef<TrackedJob>[] => [
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
    cell: ({ row }) => (
      <select
        value={row.original.status}
        onChange={(e) => handleStatusChange(row.original.tracked_job_id, e.target.value)}
        onClick={(e) => e.stopPropagation()}
        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg p-2"
      >
        <option>Saved</option>
        <option>Applied</option>
        <option>Interviewing</option>
        <option>Offer</option>
        <option>Rejected</option>
      </select>
    ),
  },
  {
    accessorKey: "relevance_score",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Relevance<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const analysis = row.original.ai_analysis;
      if (!analysis || analysis.position_relevance_score == null || analysis.environment_fit_score == null) {
        return <div className="text-center text-muted-foreground">-</div>;
      }
      const score = analysis.position_relevance_score + analysis.environment_fit_score;
      return <div className="text-center font-medium">{score}</div>
    },
    sortingFn: (rowA, rowB) => {
      const scoreA = rowA.original.ai_analysis ? rowA.original.ai_analysis.position_relevance_score + rowA.original.ai_analysis.environment_fit_score : -1;
      const scoreB = rowB.original.ai_analysis ? rowB.original.ai_analysis.position_relevance_score + rowB.original.ai_analysis.environment_fit_score : -1;
      return scoreA - scoreB;
    }
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date Saved<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => {
      const savedAt = row.original.created_at;
      if (!savedAt) { return <div className="text-center">-</div>; }
      return new Date(savedAt).toLocaleDateString();
    }
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
]