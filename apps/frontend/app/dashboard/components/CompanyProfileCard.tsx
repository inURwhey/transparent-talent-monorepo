// Path: apps/frontend/app/dashboard/components/CompanyProfileCard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Loader2 } from "lucide-react";
import { type CompanyProfile } from '../types';

interface CompanyProfileCardProps {
    companyId: number | null;
    fetchCompanyProfile: (companyId: number) => Promise<CompanyProfile | null>;
    isExpanded: boolean;
}

export default function CompanyProfileCard({ companyId, fetchCompanyProfile, isExpanded }: CompanyProfileCardProps) {
    const [profile, setProfile] = useState<CompanyProfile | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isExpanded) {
            const loadProfile = async () => {
                if (!companyId) {
                    setIsLoading(false);
                    return;
                }
                
                setIsLoading(true);
                setError(null);
                setProfile(null); // Reset profile on fetch

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
    }, [isExpanded, companyId, fetchCompanyProfile]);


    if (!isExpanded) {
        return null;
    }
    
    // Helper to format employee count
    const formatEmployeeCount = (profile: CompanyProfile | null) => {
        if (!profile) return 'N/A';
        const { company_size_min, company_size_max } = profile as any; // Using 'any' to access properties that might not be on the final type
        if (company_size_min && company_size_max) {
            return `${company_size_min.toLocaleString()} - ${company_size_max.toLocaleString()}`;
        }
        if (company_size_min) {
            return `~${company_size_min.toLocaleString()}`;
        }
        return 'N/A';
    };

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
                        {/* CORRECTED: Use the formatter with the correct properties */}
                        <p className="text-gray-800">{formatEmployeeCount(profile)}</p>
                    </div>
                    <div className="space-y-1 col-span-1 md:col-span-2">
                        <p className="font-semibold text-gray-600">Business Model</p>
                        {/* CORRECTED: Use the correct property name */}
                        <p className="text-gray-800">{profile.business_model || 'N/A'}</p>
                    </div>
                    <div className="space-y-1 col-span-1 md:col-span-2">
                        <p className="font-semibold text-gray-600">Stated Mission</p>
                         {/* CORRECTED: Use the correct property name */}
                        <p className="text-gray-800 italic">"{profile.mission || 'N/A'}"</p>
                    </div>
                </div>
            )}
        </div>
    );
}