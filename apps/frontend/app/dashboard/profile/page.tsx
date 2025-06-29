// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox'; // Added Checkbox import

// --- COMPONENT & UTILITY IMPORTS ---
// Removed DataTable and getColumns imports as they are not used on the profile page
// import { DataTable } from '../data-table'; 
// import { getColumns } from '../components/columns'; 

// --- TYPE DEFINITIONS ---
interface Profile {
    id: number;
    user_id: number;
    full_name: string | null;
    current_location: string | null;
    linkedin_profile_url: string | null;
    resume_url: string | null;
    short_term_career_goal: string | null;
    long_term_career_goals: string | null;
    desired_annual_compensation: string | null;
    desired_title: string | null;
    ideal_role_description: string | null;
    preferred_company_size: string | null;
    ideal_work_culture: string | null;
    disliked_work_culture: string | null;
    core_strengths: string | null;
    skills_to_avoid: string | null;
    non_negotiable_requirements: string | null;
    deal_breakers: string | null;
    preferred_industries: string | null;
    industries_to_avoid: string | null;
    personality_adjectives: string | null;
    personality_16_personalities: string | null;
    personality_disc: string | null;
    personality_gallup_strengths: string | null;
    preferred_work_style: string | null; // NEW FIELD
    is_remote_preferred: boolean | null; // NEW FIELD
}

// Define the shape of the data that can be sent to the PUT endpoint
type ProfileUpdatePayload = Partial<Omit<Profile, 'id' | 'user_id' | 'resume_url'>>;


export default function UserProfilePage() {
    const router = useRouter();
    const { getToken, isLoaded: isAuthLoaded } = useAuth();
    const { user, isLoaded: isUserLoaded } = useUser();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    const [profile, setProfile] = useState<Profile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    // Fetch user profile on component mount
    useEffect(() => {
        const fetchProfile = async () => {
            if (!isUserLoaded || !isAuthLoaded) return;
            setIsLoading(true);
            setError(null);
            try {
                const response = await authedFetch(`${apiBaseUrl}/api/profile`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to fetch profile.');
                }
                const data: Profile = await response.json();
                setProfile(data);
            } catch (err: any) {
                console.error("Profile fetch error:", err);
                setError(err.message || "An unexpected error occurred.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfile();
    }, [isUserLoaded, isAuthLoaded, apiBaseUrl, authedFetch]);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { id, value } = e.target;
        setProfile(prev => {
            if (!prev) return null;
            // For text/select fields, empty string means null
            return { ...prev, [id]: value === '' ? null : value };
        });
    }, []);

    // NEW: Handle checkbox changes
    const handleCheckboxChange = useCallback((id: keyof Profile, checked: boolean) => {
        setProfile(prev => {
            if (!prev) return null;
            return { ...prev, [id]: checked }; // Checkbox value is a boolean
        });
    }, []);

    const handleSubmit = useCallback(async (e: FormEvent) => {
        e.preventDefault();
        if (!profile || isSaving) return;

        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);

        // Filter out fields that are not meant to be updated via this form or are internal
        const payload: ProfileUpdatePayload = { ...profile };
        delete (payload as any).id; // Remove internal id
        delete (payload as any).user_id; // Remove internal user_id
        delete (payload as any).resume_url; // Resume URL handled separately (backlogged)

        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save profile.');
            }

            const updatedProfile: Profile = await response.json();
            // Backend should return the full updated profile, re-set it to ensure consistency
            setProfile(updatedProfile);
            setSuccessMessage("Profile saved successfully!");
            // Clear success message after a few seconds
            setTimeout(() => setSuccessMessage(null), 3000);

        } catch (err: any) {
            console.error("Profile save error:", err);
            setError(err.message || "An unexpected error occurred while saving.");
        } finally {
            setIsSaving(false);
        }
    }, [profile, isSaving, apiBaseUrl, authedFetch]);

    if (isLoading || !isUserLoaded || !isAuthLoaded) {
        return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    }

    if (error && !profile) { // Show error if initial fetch failed and no profile data is available
        return (
            <div className="min-h-screen flex items-center justify-center text-center">
                <div>
                    <h2 className="text-xl font-semibold text-red-600">Error Loading Profile</h2>
                    <p className="text-sm mt-2 text-red-700 font-mono bg-red-50 p-4 rounded-md">
                        <strong>Error Details:</strong> {error}
                    </p>
                    <Button onClick={() => window.location.reload()} className="mt-4">
                        Try Again
                    </Button>
                </div>
            </div>
        );
    }
    // If profile is null but no error, means it's still loading or just initialized.
    // The initial loading state above should cover it.
    if (!profile) return null; // Should not happen if isLoading handles initial state

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold text-gray-800 mb-6">Your Profile</h1>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                        <strong className="font-bold">Error!</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                )}
                {successMessage && (
                    <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
                        <strong className="font-bold">Success!</strong>
                        <span className="block sm:inline"> {successMessage}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Full Name */}
                    <div>
                        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
                        <Input
                            id="full_name"
                            type="text"
                            value={profile.full_name || ''}
                            onChange={handleChange}
                            className="mt-1"
                        />
                    </div>

                    {/* Short Term Career Goal */}
                    <div>
                        <label htmlFor="short_term_career_goal" className="block text-sm font-medium text-gray-700">Short-Term Career Goal</label>
                        <textarea
                            id="short_term_career_goal"
                            value={profile.short_term_career_goal || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Ideal Role Description */}
                    <div>
                        <label htmlFor="ideal_role_description" className="block text-sm font-medium text-gray-700">Ideal Role Description</label>
                        <textarea
                            id="ideal_role_description"
                            value={profile.ideal_role_description || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={5}
                        />
                    </div>

                    {/* Core Strengths */}
                    <div>
                        <label htmlFor="core_strengths" className="block text-sm font-medium text-gray-700">Core Strengths (comma-separated)</label>
                        <textarea
                            id="core_strengths"
                            value={profile.core_strengths || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Skills to Avoid */}
                    <div>
                        <label htmlFor="skills_to_avoid" className="block text-sm font-medium text-gray-700">Skills / Technologies to Avoid (comma-separated)</label>
                        <textarea
                            id="skills_to_avoid"
                            value={profile.skills_to_avoid || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>
                    
                    {/* Preferred Industries */}
                    <div>
                        <label htmlFor="preferred_industries" className="block text-sm font-medium text-gray-700">Preferred Industries (comma-separated)</label>
                        <textarea
                            id="preferred_industries"
                            value={profile.preferred_industries || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={2}
                        />
                    </div>

                    {/* Industries to Avoid */}
                    <div>
                        <label htmlFor="industries_to_avoid" className="block text-sm font-medium text-gray-700">Industries to Avoid (comma-separated)</label>
                        <textarea
                            id="industries_to_avoid"
                            value={profile.industries_to_avoid || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={2}
                        />
                    </div>

                    {/* Current Location - Using Input, which is available */}
                    <div>
                        <label htmlFor="current_location" className="block text-sm font-medium text-gray-700">Current Location</label>
                        <Input
                            id="current_location"
                            type="text"
                            value={profile.current_location || ''}
                            onChange={handleChange}
                            className="mt-1"
                        />
                    </div>

                    {/* LinkedIn Profile URL - Using Input */}
                    <div>
                        <label htmlFor="linkedin_profile_url" className="block text-sm font-medium text-gray-700">LinkedIn Profile URL</label>
                        <Input
                            id="linkedin_profile_url"
                            type="url"
                            value={profile.linkedin_profile_url || ''}
                            onChange={handleChange}
                            className="mt-1"
                            placeholder="https://www.linkedin.com/in/yourprofile/"
                        />
                    </div>

                    {/* Desired Title - Using Input */}
                    <div>
                        <label htmlFor="desired_title" className="block text-sm font-medium text-gray-700">Desired Job Title</label>
                        <Input
                            id="desired_title"
                            type="text"
                            value={profile.desired_title || ''}
                            onChange={handleChange}
                            className="mt-1"
                        />
                    </div>

                    {/* Desired Annual Compensation - Using Input */}
                    <div>
                        <label htmlFor="desired_annual_compensation" className="block text-sm font-medium text-gray-700">Desired Annual Compensation</label>
                        <Input
                            id="desired_annual_compensation"
                            type="text"
                            value={profile.desired_annual_compensation || ''}
                            onChange={handleChange}
                            className="mt-1"
                            placeholder="$150,000 - $180,000"
                        />
                    </div>

                    {/* Non-Negotiable Requirements */}
                    <div>
                        <label htmlFor="non_negotiable_requirements" className="block text-sm font-medium text-gray-700">Non-Negotiable Requirements</label>
                        <textarea
                            id="non_negotiable_requirements"
                            value={profile.non_negotiable_requirements || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Deal Breakers */}
                    <div>
                        <label htmlFor="deal_breakers" className="block text-sm font-medium text-gray-700">Deal Breakers (e.g., "On-call rotation", "Strictly in-office")</label>
                        <textarea
                            id="deal_breakers"
                            value={profile.deal_breakers || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Preferred Company Size (Using native select) */}
                    <div>
                        <label htmlFor="preferred_company_size" className="block text-sm font-medium text-gray-700">Preferred Company Size</label>
                        <select
                            id="preferred_company_size"
                            value={profile.preferred_company_size || 'null'} // Use 'null' string for actual null value
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                        >
                            <option value="null">No Preference</option>
                            <option value="Startup (1-50 employees)">Startup (1-50 employees)</option>
                            <option value="Small (51-200 employees)">Small (51-200 employees)</option>
                            <option value="Medium (201-1000 employees)">Medium (201-1000 employees)</option>
                            <option value="Large (1001-10000 employees)">Large (1001-10000 employees)</option>
                            <option value="Enterprise (10000+ employees)">Enterprise (10000+ employees)</option>
                        </select>
                    </div>

                    {/* NEW: Preferred Work Style (Using native select) */}
                    <div>
                        <label htmlFor="preferred_work_style" className="block text-sm font-medium text-gray-700">Preferred Work Style</label>
                        <select
                            id="preferred_work_style"
                            value={profile.preferred_work_style || 'null'} // Use 'null' string for actual null value
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                        >
                            <option value="null">No Preference</option>
                            <option value="On-site">On-site</option>
                            <option value="Remote">Remote</option>
                            <option value="Hybrid">Hybrid</option>
                        </select>
                    </div>

                    {/* NEW: Is Remote Preferred (Using Shadcn Checkbox) */}
                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id="is_remote_preferred"
                            checked={profile.is_remote_preferred || false} // Default to false if null
                            onCheckedChange={(checked: boolean) => handleCheckboxChange('is_remote_preferred', checked)}
                        />
                        <label
                            htmlFor="is_remote_preferred"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                            I prefer remote work generally.
                        </label>
                    </div>

                    {/* Ideal Work Culture */}
                    <div>
                        <label htmlFor="ideal_work_culture" className="block text-sm font-medium text-gray-700">Ideal Work Culture (e.g., "Collaborative", "Autonomous", "Fast-paced")</label>
                        <textarea
                            id="ideal_work_culture"
                            value={profile.ideal_work_culture || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Disliked Work Culture */}
                    <div>
                        <label htmlFor="disliked_work_culture" className="block text-sm font-medium text-gray-700">Disliked Work Culture</label>
                        <textarea
                            id="disliked_work_culture"
                            value={profile.disliked_work_culture || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Long Term Career Goals */}
                    <div>
                        <label htmlFor="long_term_career_goals" className="block text-sm font-medium text-gray-700">Long-Term Career Goals</label>
                        <textarea
                            id="long_term_career_goals"
                            value={profile.long_term_career_goals || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={3}
                        />
                    </div>

                    {/* Personality Adjectives */}
                    <div>
                        <label htmlFor="personality_adjectives" className="block text-sm font-medium text-gray-700">Personality Adjectives (e.g., "Curious", "Analytical", "Adaptable")</label>
                        <textarea
                            id="personality_adjectives"
                            value={profile.personality_adjectives || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={2}
                        />
                    </div>

                    {/* Personality 16 Personalities - Using Input */}
                    <div>
                        <label htmlFor="personality_16_personalities" className="block text-sm font-medium text-gray-700">16 Personalities Type</label>
                        <Input
                            id="personality_16_personalities"
                            type="text"
                            value={profile.personality_16_personalities || ''}
                            onChange={handleChange}
                            className="mt-1"
                            placeholder="e.g., INTJ-T"
                        />
                    </div>

                    {/* Personality DISC - Using Input */}
                    <div>
                        <label htmlFor="personality_disc" className="block text-sm font-medium text-gray-700">DISC Profile</label>
                        <Input
                            id="personality_disc"
                            type="text"
                            value={profile.personality_disc || ''}
                            onChange={handleChange}
                            className="mt-1"
                            placeholder="e.g., D-I"
                        />
                    </div>

                    {/* Personality Gallup Strengths */}
                    <div>
                        <label htmlFor="personality_gallup_strengths" className="block text-sm font-medium text-gray-700">Gallup Strengths (comma-separated)</label>
                        <textarea
                            id="personality_gallup_strengths"
                            value={profile.personality_gallup_strengths || ''}
                            onChange={handleChange}
                            className="mt-1 block w-full rounded-md border-gray-300 p-2 shadow-sm"
                            rows={2}
                        />
                    </div>

                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded">
                        {isSaving ? 'Saving...' : 'Save Profile'}
                    </Button>
                </form>
            </div>
        </main>
    );
}