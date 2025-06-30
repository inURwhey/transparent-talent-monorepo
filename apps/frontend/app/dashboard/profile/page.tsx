// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, MapPin, XCircle } from 'lucide-react';
import { type Profile } from '../types';

// Define which fields are mandatory for a user to be considered "onboarded"
const ONBOARDING_REQUIRED_FIELDS: (keyof Profile)[] = [
    'full_name',
    'short_term_career_goal',
    'work_style_preference',
    'conflict_resolution_style',
    'communication_preference',
    'change_tolerance'
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
        personalInfo: true, careerGoals: true, workEnv: true, skills: true, personality: true, workStyle: true
    });
    const toggleSection = (section: keyof typeof openSections) => {
        setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    const fetchProfile = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`);
            if (!response.ok) throw new Error('Failed to fetch profile.');
            const data: Profile = await response.json();
            setProfile(data);
        } catch (err: any) { setError(err.message); }
        finally { setIsLoading(false); }
    }, [authedFetch, apiBaseUrl]);

    useEffect(() => { if (isAuthLoaded) { fetchProfile(); } }, [isAuthLoaded, fetchProfile]);

    const handleChange = useCallback((id: keyof Profile, value: any) => {
        setProfile(prev => {
            if (!prev) return null;
            let updatedProfile = { ...prev, [id]: value === '' || value === 'null' ? null : value };
            if (id === 'preferred_work_style' && value === 'On-site') {
                updatedProfile.is_remote_preferred = false;
            }
            return updatedProfile;
        });
    }, []);

    const handleCheckboxChange = useCallback((id: keyof Profile, checked: boolean) => {
        setProfile(prev => prev ? { ...prev, [id]: checked } : null);
    }, []);

    const updateProfileData = useCallback(async (payload: Partial<Profile>) => {
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save profile.');
            }
            const updatedProfile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully!");
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsSaving(false);
        }
    }, [apiBaseUrl, authedFetch]);

    const handleSubmit = useCallback((e: FormEvent) => {
        e.preventDefault();
        if (!profile) return;
        
        const payload = { ...profile };
        delete (payload as any).id;
        delete (payload as any).user_id;
        
        // Check if all required fields are now filled
        const isOnboardingComplete = ONBOARDING_REQUIRED_FIELDS.every(field => {
            const value = payload[field];
            return value !== null && value !== '';
        });
        
        // If they are, and the user wasn't onboarded before, flip the flag
        if (isOnboardingComplete && !profile.has_completed_onboarding) {
            payload.has_completed_onboarding = true;
        }

        updateProfileData(payload);
    }, [profile, updateProfileData]);

    const handleGetLocation = useCallback(() => { /* ... (no changes) ... */ }, []);
    const handleClearLocation = useCallback(() => { /* ... (no changes) ... */ }, []);

    if (isLoading) return <div>Loading...</div>;
    if (error && !profile) return <div>Error loading profile.</div>;
    if (!profile) return null;

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold text-gray-800 mb-6">Your Profile</h1>

                {!profile.has_completed_onboarding && (
                    <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded-md" role="alert">
                        <p className="font-bold">Complete Your Profile to Unlock Your Dashboard</p>
                        <p>To ensure we find your best-fit opportunities, please complete all fields in the new "Work Style & Preferences" section, plus your "Full Name" and "Short-Term Career Goal".</p>
                    </div>
                )}

                {error && <div className="bg-red-100 border-l-4 border-red-400 text-red-700 p-4 mb-4" role="alert">{error}</div>}
                {successMessage && <div className="bg-green-100 border-l-4 border-green-400 text-green-700 p-4 mb-4" role="alert">{successMessage}</div>}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* ... (Other collapsible sections are unchanged) ... */}
                    
                    {/* --- NEW "LAYER 3" SECTION --- */}
                    <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border-2 border-indigo-300 rounded-md shadow-lg">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg bg-indigo-50">
                            Work Style & Preferences (Required) {openSections.workStyle ? <ChevronUp/> : <ChevronDown/>}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-2 space-y-4">
                            <div>
                                <Label htmlFor="work_style_preference">I do my best work in...</Label>
                                <Select value={profile.work_style_preference || 'null'} onValueChange={(value) => handleChange('work_style_preference', value)}>
                                    <SelectTrigger><SelectValue placeholder="Select a work style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="An ambiguous environment where I can create my own structure.">An ambiguous environment where I can create my own structure.</SelectItem>
                                        <SelectItem value="A structured environment with clearly defined tasks.">A structured environment with clearly defined tasks.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label htmlFor="conflict_resolution_style">When I disagree with a colleague, I prefer to...</Label>
                                <Select value={profile.conflict_resolution_style || 'null'} onValueChange={(value) => handleChange('conflict_resolution_style', value)}>
                                    <SelectTrigger><SelectValue placeholder="Select a conflict style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Have a direct, open debate to resolve the issue quickly.">Have a direct, open debate to resolve the issue quickly.</SelectItem>
                                        <SelectItem value="Build consensus with stakeholders before presenting a solution.">Build consensus with stakeholders before presenting a solution.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                             <div>
                                <Label htmlFor="communication_preference">I communicate most effectively through...</Label>
                                <Select value={profile.communication_preference || 'null'} onValueChange={(value) => handleChange('communication_preference', value)}>
                                    <SelectTrigger><SelectValue placeholder="Select a communication style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Detailed written documentation (e.g., docs, wikis, Notion).">Detailed written documentation (e.g., docs, wikis, Notion).</SelectItem>
                                        <SelectItem value="Real-time synchronous meetings (e.g., Zoom, Slack huddles).">Real-time synchronous meetings (e.g., Zoom, Slack huddles).</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label htmlFor="change_tolerance">I am most productive when...</Label>
                                <Select value={profile.change_tolerance || 'null'} onValueChange={(value) => handleChange('change_tolerance', value)}>
                                    <SelectTrigger><SelectValue placeholder="Select your preference for change..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Priorities are stable and I can focus on a long-term roadmap.">Priorities are stable and I can focus on a long-term roadmap.</SelectItem>
                                        <SelectItem value="The team is nimble and priorities pivot often based on new data.">The team is nimble and priorities pivot often based on new data.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                    
                    {/* ... (The rest of the form) ... */}
                    <Collapsible open={openSections.personalInfo} onOpenChange={() => toggleSection('personalInfo')}>
                       {/*... Full content ...*/}
                    </Collapsible>
                    <Collapsible open={openSections.careerGoals} onOpenChange={() => toggleSection('careerGoals')}>
                        {/*... Full content ...*/}
                    </Collapsible>
                    <Collapsible open={openSections.workEnv} onOpenChange={() => toggleSection('workEnv')}>
                       {/*... Full content ...*/}
                    </Collapsible>
                    <Collapsible open={openSections.skills} onOpenChange={() => toggleSection('skills')}>
                        {/*... Full content ...*/}
                    </Collapsible>
                    <Collapsible open={openSections.personality} onOpenChange={() => toggleSection('personality')}>
                        {/*... Full content ...*/}
                    </Collapsible>

                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded">
                        {isSaving ? 'Saving...' : 'Save Profile'}
                    </Button>
                </form>
            </div>
        </main>
    );
}