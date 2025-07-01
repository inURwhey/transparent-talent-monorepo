// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent, useMemo } from 'react';
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

// Define mappings for change_tolerance for two-way conversion
const changeToleranceBackendToFrontendMap: Record<string, string> = {
    'Stable': 'Priorities are stable and I can focus on a long-term roadmap.',
    'High': 'The team is nimble and priorities pivot often based on new data.',
};
const changeToleranceFrontendToBackendMap: Record<string, string> = {
    'Priorities are stable and I can focus on a long-term roadmap.': 'Stable',
    'The team is nimble and priorities pivot often based on new data.': 'High',
};

// Helper to format numbers with commas for display
const formatNumberForDisplay = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '';
    return new Intl.NumberFormat('en-US').format(num);
};

// Helper to parse formatted strings back to numbers
const parseFormattedNumber = (str: string | null | undefined): number | null => {
    if (str === null || str === undefined || str.trim() === '') return null;
    const cleaned = str.replace(/,/g, ''); // Remove commas
    const parsed = Number(cleaned);
    return isNaN(parsed) ? null : parsed;
};


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

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    const fetchProfile = useCallback(async () => {
        if (!isAuthLoaded) {
            console.log("Auth not loaded yet, skipping profile fetch.");
            return;
        }
        setIsLoading(true);
        console.log("Fetching profile data...");
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`);
            if (!response.ok) {
                throw new Error(`Failed to fetch profile. Status: ${response.status}`);
            }
            const data: Profile = await response.json();
            console.log("Profile data fetched successfully:", data);
            setProfile(data);
        } catch (err: any) {
            console.error("Error fetching profile:", err);
            setError(err.message);
        } finally {
            console.log("Finished profile fetch attempt, setting isLoading to false.");
            setIsLoading(false);
        }
    }, [isAuthLoaded, authedFetch, apiBaseUrl]);

    useEffect(() => {
        fetchProfile();
    }, [fetchProfile]);
    
    const handleChange = useCallback((id: keyof Profile, value: any) => {
        setProfile(prev => {
            if (!prev) return null;
            let actualValue: any = value;

            // Handle number inputs (desired_salary_min, desired_salary_max)
            if (id === 'desired_salary_min' || id === 'desired_salary_max') {
                actualValue = parseFormattedNumber(value); // Use helper to parse string to number
            }
            // Convert empty string from Select or Textarea to null for backend if it's the placeholder value
            else if (value === '') {
                actualValue = null;
            } 
            // Apply specific mapping for change_tolerance
            else if (id === 'change_tolerance') {
                actualValue = changeToleranceFrontendToBackendMap[value] || null; 
            }
            // For preferred_work_style and company_size, 'null' string represents no preference
            else if (value === 'null') {
                actualValue = null;
            }

            let updatedProfile = { ...prev, [id]: actualValue };

            // Special logic for is_remote_preferred based on preferred_work_style
            if (id === 'preferred_work_style' && actualValue === 'On-site') { // Use actualValue here
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
        console.log("Updating profile with payload:", payload);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, { method: 'PUT', body: JSON.stringify(payload) });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save profile.');
            const updatedProfile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully!");
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err: any) { 
            console.error("Error updating profile:", err);
            setError(err.message); 
        } 
        finally { setIsSaving(false); }
    }, [apiBaseUrl, authedFetch]);
    
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

    const handleGetLocation = useCallback(() => {
        if (!navigator.geolocation) return setError("Geolocation is not supported.");
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

    // Helper to get display value for Select components from backend value
    const getSelectDisplayValue = useCallback((field: keyof Profile) => {
        if (!profile) return ''; // Return empty string for controlled component if no profile
        const backendValue = profile[field];

        if (field === 'change_tolerance') {
            return changeToleranceBackendToFrontendMap[backendValue as string] || '';
        }
        // For other fields that are simple text values
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
                        <p>To ensure we find your best-fit opportunities, please complete all highlighted fields.</p>
                    </div>
                )}
                {error && <div className="bg-red-100 border-l-4 border-red-400 text-red-700 p-4 mb-4" role="alert"><strong className="font-bold">Error! </strong>{error}</div>}
                {successMessage && <div className="bg-green-100 border-l-4 border-green-400 text-green-700 p-4 mb-4" role="alert"><strong className="font-bold">Success! </strong>{successMessage}</div>}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border-2 border-indigo-300 rounded-md shadow-lg">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg bg-indigo-50">Work Style & Preferences (Required){openSections.workStyle ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-2 space-y-4">
                            <div><Label htmlFor="work_style_preference">I do my best work in...</Label>
                                <Select name="work_style_preference" value={getSelectDisplayValue('work_style_preference')} onValueChange={(v) => handleChange('work_style_preference',v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a work style..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="An ambiguous environment where I can create my own structure.">An ambiguous environment where I can create my own structure.</SelectItem>
                                        <SelectItem value="A structured environment with clearly defined tasks.">A structured environment with clearly defined tasks.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="conflict_resolution_style">When I disagree with a colleague, I prefer to...</Label>
                                <Select name="conflict_resolution_style" value={getSelectDisplayValue('conflict_resolution_style')} onValueChange={(v) => handleChange('conflict_resolution_style',v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a conflict style..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Have a direct, open debate to resolve the issue quickly.">Have a direct, open debate to resolve the issue quickly.</SelectItem>
                                        <SelectItem value="Build consensus with stakeholders before presenting a solution.">Build consensus with stakeholders before presenting a solution.</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="communication_preference">I communicate most effectively through...</Label>
                                <Select name="communication_preference" value={getSelectDisplayValue('communication_preference')} onValueChange={(v) => handleChange('communication_preference',v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a communication style..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Detailed written documentation (e.g., docs, wikis, Notion).">Detailed written documentation (e.g., docs, wikis, Notion).</SelectItem>
                                        <SelectItem value="Real-time synchronous meetings (e.g., Zoom, Slack huddles).">Real-time synchronous meetings (e.g., Zoom, Slack huddles).</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div><Label htmlFor="change_tolerance">I am most productive when...</Label>
                                <Select name="change_tolerance" value={getSelectDisplayValue('change_tolerance')} onValueChange={(v) => handleChange('change_tolerance',v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select your preference for change..." />
                                    </SelectTrigger>
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
                            <div><Label htmlFor="full_name">Full Name</Label><Input id="full_name" type="text" value={profile.full_name || ''} onChange={(e) => handleChange('full_name', e.target.value)} /></div>
                            <div><Label htmlFor="current_location">Current Location</Label><div className="flex items-center space-x-2"><Input id="current_location" type="text" value={profile.current_location || ''} onChange={(e) => handleChange('current_location', e.target.value)} placeholder="e.g., San Francisco, CA" className="flex-grow"/><Button type="button" onClick={handleGetLocation} disabled={isLocationLoading} variant="outline" size="icon" aria-label="Use my current location"><MapPin className="h-4 w-4" /></Button>{(profile.latitude && profile.longitude) && (<Button type="button" onClick={handleClearLocation} variant="ghost" size="icon" aria-label="Clear location"><XCircle className="h-4 w-4 text-red-500" /></Button>)}</div>
                            {(profile.latitude != null && profile.longitude != null) && <p className="text-xs text-gray-500 mt-1">Lat: {Number(profile.latitude).toFixed(4)}, Lon: {Number(profile.longitude).toFixed(4)}</p>}
                            </div>
                            <div><Label htmlFor="linkedin_profile_url">LinkedIn Profile URL</Label><Input id="linkedin_profile_url" type="url" value={profile.linkedin_profile_url || ''} onChange={(e) => handleChange('linkedin_profile_url', e.target.value)} placeholder="https://www.linkedin.com/in/yourprofile/" /></div>
                            <div><Label htmlFor="resume_url">Resume URL</Label><Input id="resume_url" type="url" value={profile.resume_url || ''} onChange={(e) => handleChange('resume_url', e.target.value)} placeholder="https://your-resume-host.com/resume.pdf" /></div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Collapsible open={openSections.careerGoals} onOpenChange={() => toggleSection('careerGoals')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Career Aspirations{openSections.careerGoals ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="short_term_career_goal">Short-Term Career Goal</Label><Textarea id="short_term_career_goal" value={profile.short_term_career_goal || ''} onChange={(e) => handleChange('short_term_career_goal', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="long_term_career_goals">Long-Term Career Goals</Label><Textarea id="long_term_career_goals" value={profile.long_term_career_goals || ''} onChange={(e) => handleChange('long_term_career_goals', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="desired_title">Desired Job Title</Label><Input id="desired_title" type="text" value={profile.desired_title || ''} onChange={(e) => handleChange('desired_title', e.target.value)} /></div>
                            
                            {/* Replaced old Desired Annual Compensation with two new fields */}
                            <div>
                                <Label htmlFor="desired_salary_min">Desired Minimum Annual Salary</Label>
                                <Input
                                    id="desired_salary_min"
                                    type="text" // Changed to text to allow comma input
                                    inputMode="numeric" // Hint for mobile keyboards
                                    pattern="[0-9,]*" // Allow digits and commas
                                    value={formatNumberForDisplay(profile.desired_salary_min)}
                                    onChange={(e) => handleChange('desired_salary_min', e.target.value)}
                                    placeholder="e.g., 150,000"
                                />
                            </div>
                            <div>
                                <Label htmlFor="desired_salary_max">Desired Maximum Annual Salary</Label>
                                <Input
                                    id="desired_salary_max"
                                    type="text" // Changed to text to allow comma input
                                    inputMode="numeric" // Hint for mobile keyboards
                                    pattern="[0-9,]*" // Allow digits and commas
                                    value={formatNumberForDisplay(profile.desired_salary_max)}
                                    onChange={(e) => handleChange('desired_salary_max', e.target.value)}
                                    placeholder="e.g., 180,000"
                                />
                            </div>

                            <div><Label htmlFor="ideal_role_description">Ideal Role Description</Label><Textarea id="ideal_role_description" value={profile.ideal_role_description || ''} onChange={(e) => handleChange('ideal_role_description', e.target.value)} rows={5} /></div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Collapsible open={openSections.workEnv} onOpenChange={() => toggleSection('workEnv')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Work Environment & Requirements{openSections.workEnv ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            {/* This preferred_work_style already uses 'null' as a placeholder value, which is fine for its own context */}
                            <div><Label htmlFor="preferred_work_style_select">Preferred Work Location</Label><Select value={profile.preferred_work_style || 'null'} onValueChange={(v) => handleChange('preferred_work_style', v)}><SelectTrigger id="preferred_work_style_select"><SelectValue placeholder="No Preference"/></SelectTrigger><SelectContent><SelectItem value="null">No Preference</SelectItem><SelectItem value="On-site">On-site</SelectItem><SelectItem value="Hybrid">Hybrid</SelectItem><SelectItem value="Remote">Remote</SelectItem></SelectContent></Select></div>
                            {profile.preferred_work_style !== 'On-site' && (<div className="flex items-center space-x-2 pl-1 pt-2"><Checkbox id="is_remote_preferred" checked={profile.is_remote_preferred || false} onCheckedChange={(checked) => handleCheckboxChange('is_remote_preferred', !!checked)} /><Label htmlFor="is_remote_preferred" className="font-normal">I prefer remote work generally.</Label></div>)}
                            <div><Label htmlFor="preferred_company_size">Preferred Company Size</Label><Select value={profile.preferred_company_size || 'null'} onValueChange={(value) => handleChange('preferred_company_size', value)}><SelectTrigger><SelectValue placeholder="No Preference" /></SelectTrigger><SelectContent><SelectItem value="null">No Preference</SelectItem><SelectItem value="Startup (1-50 employees)">Startup (1-50 employees)</SelectItem><SelectItem value="Small (51-200 employees)">Small (51-200 employees)</SelectItem><SelectItem value="Medium (201-1000 employees)">Medium (201-1000 employees)</SelectItem><SelectItem value="Large (1001-10000 employees)">Large (1001-10000 employees)</SelectItem><SelectItem value="Enterprise (10000+ employees)">Enterprise (10000+ employees)</SelectItem></SelectContent></Select></div>
                            <div><Label htmlFor="ideal_work_culture">Ideal Work Culture</Label><Textarea id="ideal_work_culture" value={profile.ideal_work_culture || ''} onChange={(e) => handleChange('ideal_work_culture', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="disliked_work_culture">Disliked Work Culture</Label><Textarea id="disliked_work_culture" value={profile.disliked_work_culture || ''} onChange={(e) => handleChange('disliked_work_culture', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="non_negotiable_requirements">Non-Negotiable Requirements</Label><Textarea id="non_negotiable_requirements" value={profile.non_negotiable_requirements || ''} onChange={(e) => handleChange('non_negotiable_requirements', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="deal_breakers">Deal Breakers</Label><Textarea id="deal_breakers" value={profile.deal_breakers || ''} onChange={(e) => handleChange('deal_breakers', e.target.value)} rows={3} /></div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Collapsible open={openSections.skills} onOpenChange={() => toggleSection('skills')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Skills & Industry Focus{openSections.skills ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="core_strengths">Core Strengths</Label><Textarea id="core_strengths" value={profile.core_strengths || ''} onChange={(e) => handleChange('core_strengths', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="skills_to_avoid">Skills / Technologies to Avoid</Label><Textarea id="skills_to_avoid" value={profile.skills_to_avoid || ''} onChange={(e) => handleChange('skills_to_avoid', e.target.value)} rows={3} /></div>
                            <div><Label htmlFor="preferred_industries">Preferred Industries</Label><Input id="preferred_industries" type="text" value={profile.preferred_industries || ''} onChange={(e) => handleChange('preferred_industries', e.target.value)} /></div>
                            <div><Label htmlFor="industries_to_avoid">Industries to Avoid</Label><Input id="industries_to_avoid" type="text" value={profile.industries_to_avoid || ''} onChange={(e) => handleChange('industries_to_avoid', e.target.value)} /></div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Collapsible open={openSections.personality} onOpenChange={() => toggleSection('personality')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Personality & Self-Assessment{openSections.personality ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                        <CollapsibleContent className="p-4 pt-0 space-y-4">
                            <div><Label htmlFor="personality_adjectives">Describe Yourself in a Few Adjectives</Label><Input id="personality_adjectives" type="text" value={profile.personality_adjectives || ''} onChange={(e) => handleChange('personality_adjectives', e.target.value)} /></div>
                            <div><Label htmlFor="personality_16_personalities">16 Personalities (e.g., INTJ)</Label><Input id="personality_16_personalities" type="text" value={profile.personality_16_personalities || ''} onChange={(e) => handleChange('personality_16_personalities', e.target.value)} /></div>
                            <div><Label htmlFor="personality_disc">DISC Profile</Label><Input id="personality_disc" type="text" value={profile.personality_disc || ''} onChange={(e) => handleChange('personality_disc', e.target.value)} /></div>
                            <div><Label htmlFor="personality_gallup_strengths">Gallup Strengths (Top 5)</Label><Textarea id="personality_gallup_strengths" value={profile.personality_gallup_strengths || ''} onChange={(e) => handleChange('personality_gallup_strengths', e.target.value)} rows={3} /></div>
                        </CollapsibleContent>
                    </Collapsible>
                    
                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700">{isSaving ? 'Saving...' : 'Save Profile'}</Button>
                </form>
            </div>
        </main>
    );
}