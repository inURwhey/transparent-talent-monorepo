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

  const buttonText = isProfileComplete ? 'Analyze' : 'Track';
  const buttonSubmittingText = isProfileComplete ? 'Analyzing...' : 'Tracking...';
  const headerText = isProfileComplete ? 'Analyze a New Job' : 'Track a New Job';

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">{headerText}</h2>
      <form onSubmit={handleSubmit}>
        <Label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700">Paste Job Posting URL</Label>
        <div className="mt-1 flex rounded-md shadow-sm">
          <Input
            type="url"
            name="jobUrl"
            id="jobUrl"
            className="block w-full flex-1 rounded-none rounded-l-md border-gray-300 p-2"
            placeholder="https://www.linkedin.com/jobs/view/..."
            value={jobUrl}
            onChange={(e) => setJobUrl(e.target.value)}
            required
          />
          <Button
            type="submit"
            className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300"
            disabled={isSubmitting}
          >
            {isSubmitting ? buttonSubmittingText : buttonText}
          </Button>
        </div>
        {submissionError && <p className="mt-2 text-sm text-red-600">{submissionError}</p>}
      </form>
    </div>
  );
}