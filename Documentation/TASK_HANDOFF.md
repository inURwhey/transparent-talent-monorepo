# Task Handoff: Implement V1 Job Matching & Recommendations

## Epic 1: Structured User Profile Data
*   **Status:** DONE

## Epic 2: Structured Job Data & V1 Matching Engine
*   **Status:** DONE

---

## Epic 3: "Jobs For You" Frontend Module
### Objective
Create and display a new "Jobs For You" module on the main user dashboard that fetches and renders a list of ranked job recommendations from the `/api/jobs/recommendations` endpoint.

### Task 3.1: Create Data Fetching Hook
*   **Acceptance Criteria:**
    *   A new file, `apps/frontend/hooks/useJobRecommendationsApi.ts`, is created.
    *   The hook correctly calls the `GET /api/jobs/recommendations` endpoint using the `authedFetch` utility.
    *   The hook manages and returns `data`, `isLoading`, and `error` states.
    *   A new `RecommendedJob` type is defined in `apps/frontend/app/dashboard/types.ts`.
*   **Relevant Files:** `apps/frontend/hooks/useJobRecommendationsApi.ts`, `apps/frontend/app/dashboard/types.ts`.
*   **Delegated To:** Flash Model

### Task 3.2: Create Display Component
*   **Acceptance Criteria:**
    *   A new file, `apps/frontend/app/dashboard/components/JobsForYou.tsx`, is created.
    *   The component receives `data`, `isLoading`, and `error` as props.
    *   It renders a loading skeleton or message while `isLoading` is true.
    *   It renders an error message if `error` is not null.
    *   It renders a list of recommended jobs, displaying the `job_title`, `company_name`, and `match_score` for each.
*   **Relevant Files:** `apps/frontend/app/dashboard/components/JobsForYou.tsx`.
*   **Delegated To:** Flash Model

### Task 3.3: Integrate Module into Dashboard
*   **Acceptance Criteria:**
    *   The main dashboard page, `apps/frontend/app/dashboard/page.tsx`, is updated.
    *   It imports and calls the `useJobRecommendationsApi` hook.
    *   It imports and renders the `JobsForYou` component, passing the hook's state as props.
    *   The new module appears on the dashboard, likely above the "My Job Tracker" table.
*   **Relevant Files:** `apps/frontend/app/dashboard/page.tsx`.
*   **Delegated To:** Flash Model

### Contextual Information & Skeletal Code

**1. Add to `apps/frontend/app/dashboard/types.ts`:**
```typescript
export interface RecommendedJob {
  id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  match_score: number;
  // Add other fields from the API response as needed
  job_modality: string | null;
  deduced_job_level: string | null;
}
```
**2. Skeletal Code for apps/frontend/hooks/useJobRecommendationsApi.ts:**
```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type RecommendedJob } from '../app/dashboard/types';

export function useJobRecommendationsApi() {
  const { getToken } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [data, setData] = useState<RecommendedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    // ... implementation for authed fetch to GET /api/jobs/recommendations
  }, [getToken, apiBaseUrl]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  return { data, isLoading, error, refetch: fetchRecommendations };
}
```
**3. Skeletal Code for apps/frontend/app/dashboard/components/JobsForYou.tsx:**
```typescript
'use client';

import { type RecommendedJob } from '../types';
import { Button } from '@/components/ui/button'; // Example import

interface JobsForYouProps {
  jobs: RecommendedJob[];
  isLoading: boolean;
  error: string | null;
}

export default function JobsForYou({ jobs, isLoading, error }: JobsForYouProps) {
  if (isLoading) {
    return <div>Loading recommendations...</div>;
  }

  if (error) {
    return <div>Error loading recommendations: {error}</div>;
  }

  if (jobs.length === 0) {
    return <div>No job recommendations available at this time.</div>;
  }

  return (
    <div className="p-4 border rounded-lg shadow-sm">
      <h2 className="text-2xl font-bold mb-4">Jobs For You</h2>
      <ul className="space-y-3">
        {jobs.map((job) => (
          <li key={job.id} className="p-3 border rounded-md">
            <h3 className="font-semibold">{job.job_title}</h3>
            <p className="text-sm text-muted-foreground">{job.company_name}</p>
            <p className="text-sm">Match Score: {job.match_score}</p>
            {/* Add buttons for 'Track' or 'Dismiss' in the future */}
          </li>
        ))}
      </ul>
    </div>
  );
}
```