// Path: apps/frontend/app/dashboard/components/JobsForYou.tsx
'use client';

import { type RecommendedJob } from '../types';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface JobsForYouProps {
  jobs: RecommendedJob[];
  isLoading: boolean;
  error: string | null;
  onTrack: (jobUrl: string) => void;
  isSubmitting: boolean;
}

export default function JobsForYou({ jobs, isLoading, error, onTrack, isSubmitting }: JobsForYouProps) {
  
  if (isLoading) {
    return (
        <div className="p-6 border rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Jobs For You</h2>
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse flex space-x-4">
                        <div className="flex-1 space-y-2 py-1">
                            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
  }

  if (error) {
    return (
        <div className="p-6 border rounded-lg shadow-md bg-red-50">
            <h2 className="text-2xl font-bold mb-4 text-red-800">Jobs For You</h2>
            <p className="text-red-700">Error loading recommendations: {error}</p>
        </div>
    );
  }

  if (jobs.length === 0) {
    return (
        <div className="p-6 border rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Jobs For You</h2>
            <p className="text-gray-600">No job recommendations available at this time. As you track more jobs, we'll learn what you like!</p>
        </div>
    );
  }

  return (
    <div className="p-6 border rounded-lg shadow-md bg-white">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Jobs For You</h2>
      <ul className="space-y-3">
        {jobs.map((job) => (
          <li key={job.id} className="p-4 border rounded-md flex justify-between items-center hover:bg-gray-50 transition-colors">
            <div>
              <Link href={job.job_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                <h3 className="font-semibold text-indigo-600">{job.job_title}</h3>
              </Link>
              <p className="text-sm text-muted-foreground">{job.company_name}</p>
              <div className="flex items-center space-x-2 text-xs mt-1">
                  <span className="font-medium">Match: {job.match_score}</span>
                  {job.job_modality && <span className="bg-gray-100 px-2 py-0.5 rounded-full">{job.job_modality}</span>}
                  {job.deduced_job_level && <span className="bg-gray-100 px-2 py-0.5 rounded-full">{job.deduced_job_level}</span>}
              </div>
            </div>
            <Button
                variant="outline"
                size="sm"
                onClick={() => onTrack(job.job_url)}
                disabled={isSubmitting}
            >
                Track
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}