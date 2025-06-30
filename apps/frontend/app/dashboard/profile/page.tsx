// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth } from '@clerk/nextjs';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, MapPin, XCircle } from 'lucide-react';
import { type Profile } from '../types';

const ONBOARDING_REQUIRED_FIELDS: (keyof Profile)[] = [
    'full_name', 'short_term_career_goal', 'work_style_preference',
    'conflict_resolution_style', 'communication_preference', 'change_tolerance'
];

export default function UserProfilePage() {
    const { getToken, isLoaded: isAuthLoaded } = useAuth();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    const [profile, setProfile] = useState<Profile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [isLocationLoading, setIsLocationLoading] = useState(false);

    const [openSections, setOpenSections] = useState({
        workStyle: true, personalInfo: true, careerGoals: true, workEnv: true, skills: true, personality: true
    });

    const toggleSection = (section: keyof typeof openSections) => {
        setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => { /* ... (no changes) ... */ }, [getToken]);
    const fetchProfile = useCallback(async () => { /* ... (no changes) ... */ }, [authedFetch, apiBaseUrl]);
    
    useEffect(() => { if (isAuthLoaded) { fetchProfile(); } }, [isAuthLoaded, fetchProfile]);

    const handleChange = useCallback((id: keyof Profile, value: any) => { /* ... (no changes) ... */ }, []);
    const handleCheckboxChange = useCallback((id: keyof Profile, checked: boolean) => { /* ... (no changes) ... */ }, []);

    const updateProfileData = useCallback(async (payload: Partial<Profile>) => { /* ... (no changes) ... */ }, [apiBaseUrl, authedFetch]);

    const handleSubmit = useCallback((e: FormEvent) => {
        e.preventDefault();
        if (!profile) return;
        const payload = { ...profile };
        delete (payload as any).id;
        delete (payload as any).user_id;
        const isOnboardingComplete = ONBOARDING_REQUIRED_FIELDS.every(field => !!payload[field]);
        if (isOnboardingComplete && !profile.has_completed_onboarding) {
            payload.has_completed_onboarding = true;
        }
        updateProfileData(payload);
    }, [profile, updateProfileData]);

    const handleGetLocation = useCallback(() => { /* ... (no changes) ... */ }, [updateProfileData]);
    const handleClearLocation = useCallback(() => { /* ... (no changes) ... */ }, [updateProfileData]);

    if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    if (error && !profile) return <div>Error loading profile...</div>;
    if (!profile) return null;

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold text-gray-800">Your Profile</h1>
                    {profile.has_completed_onboarding && (
                         <Link href="/dashboard" passHref>
                            <Button variant="outline">Back to Dashboard</Button>
                         </Link>
                    )}
                </div>

                {!profile.has_completed_onboarding && (
                    <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded-md" role="alert">
                        <p className="font-bold">Complete Your Profile to Unlock Your Dashboard</p>
                        <p>To ensure we find your best-fit opportunities, please complete all highlighted fields.</p>
                    </div>
                )}
                {/* ... (Error and Success Messages) ... */}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* --- Work Style Section --- */}
                    <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border-2 border-indigo-300 rounded-md shadow-lg">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg bg-indigo-50">Work Style & Preferences (Required){openSections.workStyle ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-2 space-y-4">
                            {/* ... (Work style select fields) ... */}
                        </CollapsibleContent>
                    </Collapsible>
                    
                    {/* --- All Other Profile Sections RESTORED --- */}
                    <Collapsible open={openSections.personalInfo} onOpenChange={() => toggleSection('personalInfo')} className="border rounded-md shadow-sm">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Contact & Basic Information {openSections.personalInfo ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="full_name">Full Name</Label><Input id="full_name" type="text" value={profile.full_name || ''} onChange={(e) => handleChange('full_name', e.target.value)} /></div>
                            <div>
                                <Label htmlFor="current_location">Current Location</Label>
                                <div className="flex items-center space-x-2">
                                    <Input id="current_location" type="text" value={profile.current_location || ''} onChange={(e) => handleChange('current_location', e.target.value)} placeholder="e.g., San Francisco, CA" className="flex-grow"/>
                                    <Button type="button" onClick={handleGetLocation} disabled={isLocationLoading} variant="outline" size="icon" aria-label="Use my current location"><MapPin className="h-4 w-4" /></Button>
                                    {(profile.latitude && profile.longitude) && (<Button type="button" onClick={handleClearLocation} variant="ghost" size="icon" aria-label="Clear location"><XCircle className="h-4 w-4 text-red-500" /></Button>)}
                                </div>
                                {(profile.latitude && profile.longitude) && <p className="text-xs text-gray-500 mt-1">Lat: {profile.latitude.toFixed(4)}, Lon: {profile.longitude.toFixed(4)}</p>}
                            </div>
                            <div><Label htmlFor="linkedin_profile_url">LinkedIn Profile URL</Label><Input id="linkedin_profile_url" type="url" value={profile.linkedin_profile_url || ''} onChange={(e) => handleChange('linkedin_profile_url', e.target.value)} placeholder="https://www.linkedin.com/in/yourprofile/" /></div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Collapsible open={openSections.careerGoals} onOpenChange={() => toggleSection('careerGoals')} className="border rounded-md shadow-sm">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Career Aspirations {openSections.careerGoals ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="short_term_career_goal">Short-Term Career Goal</Label><Textarea id="short_term_career_goal" value={profile.short_term_career_goal || ''} onChange={(e) => handleChange('short_term_career_goal', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="long_term_career_goals">Long-Term Career Goals</Label><Textarea id="long_term_career_goals" value={profile.long_term_career_goals || ''} onChange={(e) => handleChange('long_term_career_goals', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="desired_title">Desired Job Title</Label><Input id="desired_title" type="text" value={profile.desired_title || ''} onChange={(e) => handleChange('desired_title', e.target.value)} /></div>
                            <div><Label htmlFor="desired_annual_compensation">Desired Annual Compensation</Label><Input id="desired_annual_compensation" type="text" value={profile.desired_annual_compensation || ''} onChange={(e) => handleChange('desired_annual_compensation', e.target.value)} placeholder="$150,000 - $180,000" /></div>
                            <div><Label htmlFor="ideal_role_description">Ideal Role Description</Label><Textarea id="ideal_role_description" value={profile.ideal_role_description || ''} onChange={(e) => handleChange('ideal_role_description', e.target.value)} rows={5} /></div>
                        </CollapsibleContent>
                    </Collapsible>
                    
                    {/* ... other sections ... */}

                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded">{isSaving ? 'Saving...' : 'Save Profile'}</Button>
                </form>
            </div>
        </main>
    );
}