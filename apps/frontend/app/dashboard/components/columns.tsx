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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

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
  is_excited: boolean;
  job_posting_status: string; // Added from 'jobs' table
  last_checked_at: string | null; // Added from 'jobs' table
  status_reason: string | null; // Added for 'tracked_jobs' table
  ai_analysis: AIAnalysis | null;
}

// --- PROPS FOR THE GETCOLUMNS FUNCTION ---
interface GetColumnsProps {
  handleStatusChange: (trackedJobId: number, newStatus: string) => void;
  handleRemoveJob: (trackedJobId: number) => void;
  handleToggleExcited: (trackedJobId: number, isExcited: boolean) => void;
}

// This function generates the column definitions.
// It takes callbacks as arguments to keep the column logic separate from the page logic.
export const getColumns = ({ handleStatusChange, handleRemoveJob, handleToggleExcited }: GetColumnsProps): ColumnDef<TrackedJob>[] => [
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
      <Select
        value={row.original.status}
        onValueChange={(newValue) => handleStatusChange(row.original.tracked_job_id, newValue)}
      >
        <SelectTrigger className="w-[180px] bg-gray-50">
          <SelectValue placeholder="Select Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="Saved">Saved</SelectItem>
          <SelectItem value="Applied">Applied</SelectItem>
          <SelectItem value="Interviewing">Interviewing</SelectItem>
          <SelectItem value="Offer">Offer</SelectItem>
          <SelectItem value="Rejected">Rejected</SelectItem>
          <SelectItem value="Expired">Expired</SelectItem> {/* Added Expired status */}
          <SelectItem value="Withdrawn">Withdrawn</SelectItem> {/* Added Withdrawn status */}
          <SelectItem value="Accepted">Accepted</SelectItem> {/* Added Accepted status */}
        </SelectContent>
      </Select>
    ),
  },
  {
    accessorKey: "status_reason", // NEW COLUMN: Status Reason for Tracked Job
    header: "Status Reason",
    cell: ({ row }) => {
      const reason = row.original.status_reason;
      return <div className="text-sm text-muted-foreground">{reason || "-"}</div>;
    },
  },
  {
    accessorKey: "job_posting_status", // NEW COLUMN: Job Posting Status
    header: "Job Post Status",
    cell: ({ row }) => {
      const status = row.original.job_posting_status;
      const lastChecked = row.original.last_checked_at;
      const formattedDate = lastChecked ? new Date(lastChecked).toLocaleDateString() : 'N/A';
      
      let textColor = "text-gray-700";
      if (status === "Active") {
        textColor = "text-green-600";
      } else if (status && status.includes("Expired")) {
        textColor = "text-red-600";
      }

      return (
        <div className={`font-medium ${textColor}`}>
          {status || "Unknown"}
          {lastChecked && <div className="text-xs text-muted-foreground mt-0.5">Checked: {formattedDate}</div>}
        </div>
      );
    },
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
    accessorKey: "is_excited",
    header: "Excited?",
    cell: ({ row }) => (
      <div className="flex items-center justify-center">
        <Checkbox
          checked={row.original.is_excited}
          onCheckedChange={(checked: boolean) => {
            handleToggleExcited(row.original.tracked_job_id, checked);
          }}
        />
      </div>
    ),
    enableSorting: true,
    enableHiding: true,
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