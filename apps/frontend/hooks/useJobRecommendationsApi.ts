// Path: apps/frontend/hooks/useJobRecommendationsApi.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type RecommendedJob } from '../app/dashboard/types';

export function useJobRecommendationsApi() {
  const { getToken, isLoaded } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [data, setData] = useState<RecommendedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    if (!isLoaded) return; // Wait until auth is loaded
    setIsLoading(true);
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available.");
      }

      const response = await fetch(`${apiBaseUrl}/api/jobs/recommendations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch recommendations. Status: ${response.status}`);
      }
      
      const responseData: RecommendedJob[] = await response.json();
      setData(responseData);

    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.');
      console.error("Failed to fetch job recommendations:", err);
    } finally {
      setIsLoading(false);
    }
  }, [getToken, apiBaseUrl, isLoaded]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  return { data, isLoading, error, refetch: fetchRecommendations };
}