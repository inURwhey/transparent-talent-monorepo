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
      
      const responseData = await response.json();
      
      // THE FIX: Check if the response is an object with a 'jobs' property,
      // otherwise, default to an empty array to prevent map errors.
      if (responseData && Array.isArray(responseData.jobs)) {
          setData(responseData.jobs);
      } else if (Array.isArray(responseData)) {
          // Fallback for if the API returns a simple array
          setData(responseData);
      } else {
          console.warn("Received unexpected data structure for recommendations:", responseData);
          setData([]); // Ensure data is an array to prevent crashes.
      }

    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.');
      console.error("Failed to fetch job recommendations:", err);
      setData([]); // CRITICAL: Ensure data is an empty array on error.
    } finally {
      setIsLoading(false);
    }
  }, [getToken, apiBaseUrl, isLoaded]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  return { data, isLoading, error, refetch: fetchRecommendations };
}