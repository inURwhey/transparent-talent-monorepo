// Path: apps/frontend/app/dashboard/components/CompanyProfileCard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Loader2 } from "lucide-react";
import { type CompanyProfile } from '../types';

interface CompanyProfileCardProps {
    companyId: number;
    fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
    isExpanded: boolean;
}

export default function CompanyProfileCard({ companyId, fetchCompanyProfile, isExpanded }: CompanyProfileCardProps) {
    const [profile, setProfile] = useState<CompanyProfile | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // This effect should ONLY run when the component is expanded for the first time.
        // We check `isExpanded` to trigger it, and `!profile` to ensure it only runs once.
        if (isExpanded && !profile && !isLoading) {
            const loadProfile = async () => {
                setIsLoading(true);
                setError(null);
                try {
                    const fetchedProfile = await fetchCompanyProfile(companyId);
                    setProfile(fetchedProfile);
                } catch (err) {
                    setError("Failed to load company data.");
                    console.error(err);
                } finally {
                    setIsLoading(false);
                }
            };

            loadProfile();
        }
    // This simplified dependency array is key. It re-evaluates the effect
    // when `isExpanded` changes, which is exactly what we need.
    }, [isExpanded, companyId, fetchCompanyProfile, profile, isLoading]);

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