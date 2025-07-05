// Path: apps/frontend/app/dashboard/components/columns.tsx
"use client"

import { ColumnDef } from "@tanstack/react-table"
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
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Textarea } from "@/components/ui/textarea"
import React from "react"
import { type TrackedJob, type UpdatePayload } from '../types'
import { cn } from "@/lib/utils"
import { format } from "date-fns"

interface GetColumnsProps {
  handleUpdateJobField: (trackedJobId: number, field: keyof UpdatePayload, value: any) => Promise<void>;
  handleRemoveJob: (trackedJobId: number) => void;
}

const SUCCESS_STATUSES = ['OFFER_ACCEPTED'];
const NEGATIVE_TERMINAL_STATUSES = ['REJECTED', 'EXPIRED'];
const NEUTRAL_TERMINAL_STATUSES = ['WITHDRAWN'];
const ACTIVE_STATUSES = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS'];

export const getColumns = ({
  handleUpdateJobField,
  handleRemoveJob,
}: GetColumnsProps): ColumnDef<TrackedJob>[] => [
  {
    id: "select",
    header: ({ table }) => (<Checkbox checked={table.getIsAllPageRowsSelected()} onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)} aria-label="Select all" />),
    cell: ({ row }) => (<Checkbox checked={row.getIsSelected()} onCheckedChange={(value) => row.toggleSelected(!!value)} aria-label="Select row" />),
    enableSorting: false,
    enableHiding: false,
  },
  {
    id: "expander",
    header: () => null,
    cell: ({ row }) => (
      <Button variant="ghost" size="icon" onClick={() => row.toggleExpanded()}>
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
    cell: ({ row }) => row.original.ai_grade ? <div className="text-center font-medium">{row.original.ai_grade}</div> : <div className="text-center text-gray-400 italic">N/A</div>,
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
          onValueChange={(newValue) => handleUpdateJobField(row.original.id, 'status', newValue)}
        >
          <SelectTrigger id={`status-select-${row.original.id}`} className="w-[140px] bg-gray-50">
            <SelectValue className={textColor} placeholder="Select Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="SAVED" className="text-blue-600">Saved</SelectItem>
            <SelectItem value="APPLIED" className="text-blue-600">Applied</SelectItem>
            <SelectItem value="INTERVIEWING" className="text-blue-600">Interviewing</SelectItem>
            <SelectItem value="OFFER_NEGOTIATIONS" className="text-blue-600">Offer</SelectItem>
            <SelectItem value="REJECTED" className="text-red-600">Rejected</SelectItem>
            <SelectItem value="EXPIRED" className="text-red-600">Expired</SelectItem>
            <SelectItem value="WITHDRAWN" className="text-gray-600">Withdrawn</SelectItem>
            <SelectItem value="OFFER_ACCEPTED" className="text-green-600">Accepted</SelectItem>
          </SelectContent>
        </Select>
      );
    },
  },
  {
    accessorKey: "is_excited",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Excited?<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => ( <div className="text-center"><Checkbox checked={row.original.is_excited} onCheckedChange={(checked: boolean) => handleUpdateJobField(row.original.id, 'is_excited', checked)}/></div>),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (<Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date Saved<ArrowUpDown className="ml-2 h-4 w-4" /></Button>),
    cell: ({ row }) => (new Date(row.original.created_at).toLocaleDateString()),
  },
  {
    accessorKey: 'applied_at',
    header: 'Date Applied',
    cell: ({ row }) => (row.original.applied_at ? new Date(row.original.applied_at).toLocaleDateString() : 'N/A'),
  },
  {
    accessorKey: 'next_action_at',
    header: 'Next Action Date',
    cell: ({ row }) => {
        const [date, setDate] = React.useState<Date | undefined>(
            row.original.next_action_at ? new Date(row.original.next_action_at) : undefined
        );
        const today = new Date();
        today.setHours(0,0,0,0);

        return (
            <Popover>
                <PopoverTrigger asChild>
                    <Button
                        variant={"outline"}
                        className={cn("w-full justify-start text-left font-normal", !date && "text-muted-foreground")}
                    >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : <span>Pick a date</span>}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                        mode="single"
                        selected={date}
                        onSelect={(newDate) => {
                            setDate(newDate);
                            handleUpdateJobField(row.original.id, 'next_action_at', newDate ? newDate.toISOString() : null);
                        }}
                        disabled={(date) => date < today }
                        initialFocus
                    />
                     <div className="p-2 border-t border-border">
                        <Button
                            variant="ghost"
                            size="sm"
                            className="w-full justify-center"
                            onClick={() => {
                                setDate(undefined);
                                handleUpdateJobField(row.original.id, 'next_action_at', null);
                            }}
                        >
                            Clear Date
                        </Button>
                    </div>
                </PopoverContent>
            </Popover>
        );
    },
  },
  {
    accessorKey: "next_action_notes",
    header: "Next Action Notes",
    cell: ({ row }) => (
      <Textarea
        defaultValue={row.original.next_action_notes ?? ""}
        onBlur={(e) => handleUpdateJobField(row.original.id, 'next_action_notes', e.target.value)}
        placeholder="Next action..."
        className="w-[200px]"
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
            <DropdownMenuItem onClick={() => window.open(job.job_opportunity.url, '_blank')}>View Original Post</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600 focus:text-red-500" onClick={() => handleRemoveJob(job.id)}>
              <Trash2 className="mr-2 h-4 w-4" /> Remove from Tracker
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
];