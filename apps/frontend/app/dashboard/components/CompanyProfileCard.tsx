// Path: apps/frontend/app/dashboard/components/CompanyProfileCard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Loader2 } from "lucide-react";
import { type CompanyProfile } from '../types';

interface CompanyProfileCardProps {
    companyId: number;
    fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
}

export default function CompanyProfileCard({ companyId, fetchCompanyProfile }: CompanyProfileCardProps) {
    const [profile, setProfile] = useState<CompanyProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true; // Flag to track if the component is mounted

        const loadProfile = async () => {
            if (!companyId) {
                setIsLoading(false);
                return;
            };
            
            setIsLoading(true);
            setError(null);

            try {
                const fetchedProfile = await fetchCompanyProfile(companyId);
                if (isMounted) { // Only update state if the component is still mounted
                    setProfile(fetchedProfile);
                }
            } catch (err) {
                if (isMounted) {
                    setError("Failed to load company data.");
                }
                console.error(err);
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        };

        loadProfile();

        // Cleanup function to run when the component unmounts
        return () => {
            isMounted = false;
        };
    // The dependency array ensures this effect runs only when companyId changes.
    }, [companyId, fetchCompanyProfile]);

    return (
        <div className="p-4 bg-gray-50/50 border-l-4 border-blue-500">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Company Snapshot</h3>
            {isLoading && (
                <div className="flex items-center text-gray-500">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    <span>Loading company profile...</span>
                </div>
            )}
            {!isLoading && error && (
                 <p className="text-red-500 text-sm">{error}</p>
            )}
            {!isLoading && !error && !profile && (
                <p className="text-gray-500 text-sm">No AI-generated company profile is available yet.</p>
            )}
            {!isLoading && !error && profile && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="space-y-1">
                        <p className="font-semibold text-gray-600">Industry</p>
                        <p className="text-gray-800">{profile.industry || 'N/A'}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="font-semibold text-gray-600">Employee Count</p>
                        <p className="text-gray-800">{profile.employee_count_range || 'N/A'}</p>
                    </div>
                    <div className="space-y-1 col-span-1 md:col-span-2">
                        <p className="font-semibold text-gray-600">Business Model</p>
                        <p className="text-gray-800">{profile.primary_business_model || 'N/A'}</p>
                    </div>
                    <div className="space-y-1 col-span-1 md:col-span-2">
                        <p className="font-semibold text-gray-600">Stated Mission</p>
                        <p className="text-gray-800 italic">"{profile.publicly_stated_mission || 'N/A'}"</p>
                    </div>
                </div>
            )}
        </div>
    );
}