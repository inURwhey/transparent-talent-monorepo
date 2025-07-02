// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, MapPin, XCircle } from 'lucide-react';
import { type Profile } from '@/app/dashboard/types';

const ONBOARDING_REQUIRED_FIELDS: (keyof Profile)[] = [
    'work_style_preference',
    'conflict_resolution_style',
    'communication_preference',
    'change_tolerance',
    'short_term_career_goal',
    'desired_title'
];

const changeToleranceBackendToFrontendMap: Record<string, string> = {
    'Stable': 'Priorities are stable and I can focus on a long-term roadmap.',
    'High': 'The team is nimble and priorities pivot often based on new data.',
};
const changeToleranceFrontendToBackendMap: Record<string, string> = {
    'Priorities are stable and I can focus on a long-term roadmap.': 'Stable',
    'The team is nimble and priorities pivot often based on new data.': 'High',
};

const formatNumberForDisplay = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '';
    return new Intl.NumberFormat('en-US').format(num);
};

const parseFormattedNumber = (str: string | null | undefined): number | null => {
    if (str === null || str === undefined || str.trim() === '') return null;
    const cleaned = str.replace(/,/g, '');
    const parsed = Number(cleaned);
    return isNaN(parsed) ? null : parsed;
};

export default function UserProfilePage() {
    const { getToken, isLoaded: isAuthLoaded } = useAuth();
    const router = useRouter();
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

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    const fetchProfile = useCallback(async () => {
        if (!isAuthLoaded) return;
        setIsLoading(true);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`);
            if (!response.ok) throw new Error('Failed to fetch profile.');
            const data: Profile = await response.json();
            setProfile(data);
        } catch (err: any) { setError(err.message); } 
        finally { setIsLoading(false); }
    }, [isAuthLoaded, authedFetch, apiBaseUrl]);

    useEffect(() => { fetchProfile(); }, [fetchProfile]);
    
    const handleChange = useCallback((id: keyof Profile, value: any) => {
        setProfile(prev => {
            if (!prev) return null;
            let actualValue: any = value;
            if (id === 'desired_salary_min' || id === 'desired_salary_max') {
                actualValue = parseFormattedNumber(value);
            } else if (value === '') {
                actualValue = null;
            } else if (id === 'change_tolerance') {
                actualValue = changeToleranceFrontendToBackendMap[value] || null; 
            } else if (value === 'null') {
                actualValue = null;
            }
            let updatedProfile = { ...prev, [id]: actualValue };
            if (id === 'preferred_work_style' && actualValue === 'On-site') {
                updatedProfile.is_remote_preferred = false;
            }
            return updatedProfile;
        });
    }, []);

    const handleCheckboxChange = useCallback((id: keyof Profile, checked: boolean) => {
        setProfile(prev => (prev ? { ...prev, [id]: checked } : null));
    }, []);

    const updateProfileData = useCallback(async (payload: Partial<Omit<Profile, 'id' | 'user_id'>>) => {
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, { method: 'PUT', body: JSON.stringify(payload) });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save profile.');
            const updatedProfile: Profile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully! Redirecting to dashboard...");
            setTimeout(() => {
                window.location.assign('/dashboard');
            }, 1500);
        } catch (err: any) { 
            console.error("Error updating profile:", err);
            setError(err.message); 
            setIsSaving(false);
        }
    }, [apiBaseUrl, authedFetch]);
    
    const handleSubmit = useCallback((e: FormEvent) => {
        e.preventDefault();
        if (!profile) return;
        let payload: Partial<Profile> = { ...profile };
        delete (payload as any).id;
        delete (payload as any).user_id;
        updateProfileData(payload);
    }, [profile, updateProfileData]);

    const handleGetLocation = useCallback(() => {
        if (!navigator.geolocation) return setError("Geolocation is not supported by your browser.");
        setIsLocationLoading(true);
        navigator.geolocation.getCurrentPosition(
            (position) => {
                updateProfileData({ latitude: position.coords.latitude, longitude: position.coords.longitude });
                setIsLocationLoading(false);
            },
            (error) => {
                setError(`Geolocation error: ${error.message}`);
                setIsLocationLoading(false);
            }
        );
    }, [updateProfileData]);

    const handleClearLocation = useCallback(() => {
        updateProfileData({ latitude: null, longitude: null, current_location: '' });
    }, [updateProfileData]);

    const getSelectDisplayValue = useCallback((field: keyof Profile) => {
        if (!profile) return '';
        const backendValue = profile[field];
        if (field === 'change_tolerance') {
            return changeToleranceBackendToFrontendMap[backendValue as string] || '';
        }
        return (backendValue as string) || '';
    }, [profile]);

    if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    if (!profile) return <div className="min-h-screen flex items-center justify-center">Could not load profile. Please try refreshing the page.</div>;

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold text-gray-800">Your Profile</h1>
                    {profile.has_completed_onboarding && (<Link href="/dashboard" passHref><Button variant="outline">Back to Dashboard</Button></Link>)}
                </div>
                {!profile.has_completed_onboarding && (
                    <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded-md" role="alert">
                        <p className="font-bold">Complete Your Profile to Unlock Your Dashboard</p>
                        <p>To ensure we find your best-fit opportunities, please complete all highlighted fields marked with a <span className="text-red-500 font-bold">*</span> and submit a resume via the Welcome page.</p>
                    </div>
                )}
                {error && <div className="bg-red-100 border-l-4 border-red-400 text-red-700 p-4 mb-4" role="alert"><strong className="font-bold">Error! </strong>{error}</div>}
                {successMessage && <div className="bg-green-100 border-l-4 border-green-400 text-green-700 p-4 mb-4" role="alert"><strong className="font-bold">Success! </strong>{successMessage}</div>}
                <form onSubmit={handleSubmit} className="space-y-6">
                    <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border-2 border-indigo-300 rounded-md shadow-lg">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg bg-indigo-50">Work Style & Preferences <span className="font-bold text-red-500 ml-2">*Required</span>{openSections.workStyle ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-2 space-y-4">
                            <div><Label htmlFor="work_style_preference">I do my best work in... <span className="text-red-500">*</span></Label>
                                <Select name="work_style_preference" value={getSelectDisplayValue('work_style_preference')} onValueChange={(v) => handleChange('work_style_preference',v)}>
                                    <SelectTrigger><SelectValue placeholder="Select a work style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="An ambiguous environment where I can create my own structure.">An ambiguous environment where I can create my own structure.</SelectItem>
                                        <SelectItem value="A structured environment with clearly defined tasks.">A structured environment with clearly defined tasks.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="conflict_resolution_style">When I disagree with a colleague, I prefer to... <span className="text-red-500">*</span></Label>
                                <Select name="conflict_resolution_style" value={getSelectDisplayValue('conflict_resolution_style')} onValueChange={(v) => handleChange('conflict_resolution_style',v)}>
                                    <SelectTrigger><SelectValue placeholder="Select a conflict style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Have a direct, open debate to resolve the issue quickly.">Have a direct, open debate to resolve the issue quickly.</SelectItem>
                                        <SelectItem value="Build consensus with stakeholders before presenting a solution.">Build consensus with stakeholders before presenting a solution.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="communication_preference">I communicate most effectively through... <span className="text-red-500">*</span></Label>
                                <Select name="communication_preference" value={getSelectDisplayValue('communication_preference')} onValueChange={(v) => handleChange('communication_preference',v)}>
                                    <SelectTrigger><SelectValue placeholder="Select a communication style..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Detailed written documentation (e.g., docs, wikis, Notion).">Detailed written documentation (e.g., docs, wikis, Notion).</SelectItem>
                                        <SelectItem value="Real-time synchronous meetings (e.g., Zoom, Slack huddles).">Real-time synchronous meetings (e.g., Zoom, Slack huddles).</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="change_tolerance">I am most productive when... <span className="text-red-500">*</span></Label>
                                <Select name="change_tolerance" value={getSelectDisplayValue('change_tolerance')} onValueChange={(v) => handleChange('change_tolerance',v)}>
                                    <SelectTrigger><SelectValue placeholder="Select your preference for change..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Priorities are stable and I can focus on a long-term roadmap.">Priorities are stable and I can focus on a long-term roadmap.</SelectItem>
                                        <SelectItem value="The team is nimble and priorities pivot often based on new data.">The team is nimble and priorities pivot often based on new data.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                    <Collapsible open={openSections.personalInfo} onOpenChange={() => toggleSection('personalInfo')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Contact & Basic Information{openSections.personalInfo ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            {/* ... Fields unchanged ... */}
                        </CollapsibleContent>
                    </Collapsible>
                    <Collapsible open={openSections.careerGoals} onOpenChange={() => toggleSection('careerGoals')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Career Aspirations <span className="font-bold text-red-500 ml-2">*Required</span>{openSections.careerGoals ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="short_term_career_goal">Short-Term Career Goal <span className="text-red-500">*</span></Label><Textarea id="short_term_career_goal" value={profile.short_term_career_goal || ''} onChange={(e) => handleChange('short_term_career_goal', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="long_term_career_goals">Long-Term Career Goals</Label><Textarea id="long_term_career_goals" value={profile.long_term_career_goals || ''} onChange={(e) => handleChange('long_term_career_goals', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="desired_title">Desired Job Title <span className="text-red-500">*</span></Label><Input id="desired_title" type="text" value={profile.desired_title || ''} onChange={(e) => handleChange('desired_title', e.target.value)} /></div>
                            {/* ... Fields unchanged ... */}
                        </CollapsibleContent>
                    </Collapsible>
                    {/* ... Other collapsibles ... */}
                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700">{isSaving ? 'Saving...' : 'Save Profile'}</Button>
                </form>
            </div>
        </main>
    );
}