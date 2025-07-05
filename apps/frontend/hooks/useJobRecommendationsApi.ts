// Path: apps/frontend/hooks/useJobRecommendationsApi.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/nextjs';
import { type RecommendedJob, type Profile } from '../app/dashboard/types';

export function useJobRecommendationsApi(profile: Profile | null) {
  const { getToken, isLoaded } = useAuth();
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [data, setData] = useState<RecommendedJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    // Don't fetch if auth isn't ready or if the profile object doesn't exist yet.
    if (!isLoaded || !profile) return; 
    
    // Only fetch if the user has completed onboarding.
    if (!profile.has_completed_onboarding) {
        setData([]);
        setIsLoading(false);
        return;
    }

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
      
      if (responseData && Array.isArray(responseData.jobs)) {
          setData(responseData.jobs);
      } else if (Array.isArray(responseData)) {
          setData(responseData);
      } else {
          console.warn("Received unexpected data structure for recommendations:", responseData);
          setData([]);
      }

    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.');
      console.error("Failed to fetch job recommendations:", err);
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, [getToken, apiBaseUrl, isLoaded, profile]); // CRITICAL FIX: Add profile to dependency array

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  return { data, isLoading, error, refetch: fetchRecommendations };
}