// Path: apps/frontend/app/dashboard/components/JobSubmissionForm.tsx
'use client';

import { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface JobSubmissionFormProps {
  isSubmitting: boolean;
  submissionError: string | null;
  onSubmit: (jobUrl: string) => Promise<void>;
  isProfileComplete: boolean;
}

export function JobSubmissionForm({ isSubmitting, submissionError, onSubmit, isProfileComplete }: JobSubmissionFormProps) {
  const [jobUrl, setJobUrl] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!jobUrl.trim() || isSubmitting) return;
    await onSubmit(jobUrl);
    if (!submissionError) {
        setJobUrl('');
    }
  };

  const buttonText = isProfileComplete ? 'Analyze Job' : 'Track Job';
  const buttonSubmittingText = isProfileComplete ? 'Analyzing...' : 'Tracking...';
  const headerText = isProfileComplete ? 'Analyze a New Job' : 'Track a New Job';
  const descriptionText = isProfileComplete 
    ? "Paste a job URL to get a detailed AI analysis and relevance score based on your complete profile."
    : "Your profile is incomplete. Paste a job URL to track it now. Complete your profile to unlock AI analysis.";

  return (
    <div className="bg-white p-6 rounded-lg shadow-md h-full flex flex-col">
      <h2 className="text-2xl font-semibold text-gray-800 mb-2">{headerText}</h2>
      <p className="text-sm text-gray-600 mb-4">{descriptionText}</p>
      <form onSubmit={handleSubmit} className="flex flex-col flex-grow">
        <div className="flex-grow">
          <Label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700">
            Job Posting URL
          </Label>
          <Input
            type="url"
            name="jobUrl"
            id="jobUrl"
            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="https://www.linkedin.com/jobs/view/..."
            value={jobUrl}
            onChange={(e) => setJobUrl(e.target.value)}
            required
          />
        </div>
        <div className="mt-4">
          <Button
            type="submit"
            className="w-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300"
            disabled={isSubmitting || !jobUrl.trim()}
          >
            {isSubmitting ? buttonSubmittingText : buttonText}
          </Button>
        </div>
        {submissionError && <p className="mt-2 text-sm text-red-600">{submissionError}</p>}
      </form>
    </div>
  );
}