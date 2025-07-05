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
import { type Profile } from '@/app/dashboard/types';
import { ResumeUploadForm } from '../components/ResumeUploadForm';

const ONBOARDING_REQUIRED_FIELDS: (keyof Profile)[] = [
    'work_style_preference',
    'conflict_resolution_style',
    'communication_preference',
    'change_tolerance',
    'career_goals',
    'desired_job_titles'
];

// CORRECTED: `value` now matches the backend ENUM, `label` is human-readable.
const companySizeOptions = [
    { value: 'NO_PREFERENCE', label: 'No Preference' },
    { value: 'STARTUP', label: 'Startup (1-50 employees)' },
    { value: 'SMALL_BUSINESS', label: 'Small Business (1-50 employees)' },
    { value: 'MEDIUM_BUSINESS', label: 'Medium Business (51-250 employees)' },
    { value: 'LARGE_ENTERPRISE', label: 'Large Enterprise (250+ employees)' },
];

const workStyleOptions = [
    { value: 'NO_PREFERENCE', label: 'I am open to any work style.' },
    { value: 'STRUCTURED', label: 'I prefer a structured environment with clear processes and predictable day-to-day tasks.' },
    { value: 'AUTONOMOUS', label: 'I prefer to work autonomously where I can be independent and self-directed.' },
    { value: 'COLLABORATIVE', label: 'I prefer a collaborative atmosphere that is team-oriented with frequent interaction.' },
    { value: 'HYBRID', label: 'I prefer a hybrid work style that offers a mix of structure and autonomy.' },
];

const conflictResolutionOptions = [
    { value: 'NO_PREFERENCE', label: 'I am comfortable with any approach to conflict resolution.' },
    { value: 'DIRECT', label: 'I prefer to address conflict directly through face-to-face or immediate conversations.' },
    { value: 'MEDIATED', label: 'I prefer a mediated approach to conflict that involves a neutral third party.' },
    { value: 'AVOIDANT', label: 'I prefer to de-escalate or avoid conflict when possible.' },
];

const communicationPreferenceOptions = [
    { value: 'NO_PREFERENCE', label: 'I am adaptable to any communication style.' },
    { value: 'WRITTEN', label: 'I prefer written communication, such as email and detailed documentation.' },
    { value: 'VERBAL', label: 'I prefer verbal communication, like meetings and phone calls.' },
    { value: 'VISUAL', label: 'I prefer visual communication methods, including diagrams and presentations.' },
];

const changeToleranceOptions = [
    { value: 'NO_PREFERENCE', label: 'I am open to various levels of change.' },
    { value: 'HIGH', label: 'I prefer a high-change environment and thrive in fast-paced, evolving workplaces.' },
    { value: 'MEDIUM', label: 'I prefer a medium level of change where I can adapt but also have some stability.' },
    { value: 'LOW', label: 'I prefer a low-change environment with stability and established routines.' },
];

const preferredWorkLocationOptions = [
    { value: 'NO_PREFERENCE', label: 'No Preference' },
    { value: 'ON_SITE', label: 'On-site' },
    { value: 'HYBRID', label: 'Hybrid' },
    { value: 'REMOTE', label: 'Remote' },
];


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
            } else if (value === 'null' || value === '' || value === 'NO_PREFERENCE') {
                // Treat "NO_PREFERENCE" from dropdowns as null for saving, but the component will handle display
                actualValue = null;
            }

            let updatedProfile = { ...prev, [id]: actualValue };

            if (id === 'preferred_work_style' && actualValue !== 'HYBRID') {
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
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to save profile.');
            const updatedProfile: Profile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully!");
        } catch (err: any) {
            console.error("Error updating profile:", err);
            setError(err.message);
        } finally {
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
        updateProfileData({ latitude: null, longitude: null, location: '' });
    }, [updateProfileData]);

    const isRequired = (field: keyof Profile) => !profile?.has_completed_onboarding && ONBOARDING_REQUIRED_FIELDS.includes(field);

    if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    if (!profile) return <div className="min-h-screen flex items-center justify-center">Could not load profile. Please try refreshing the page.</div>;

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="bg-white p-8 rounded-lg shadow-md">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-3xl font-bold text-gray-800">Your Profile</h1>
                    </div>
                    {!profile.has_completed_onboarding && (
                        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded-md" role="alert">
                            <p className="font-bold">Complete Your Profile to Unlock AI Analysis</p>
                            <p>To find your best-fit opportunities, please submit a resume (at the bottom of this page) and fill out all fields marked with a <span className="text-red-500 font-bold">*</span>.</p>
                        </div>
                    )}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Work Style Preferences Section */}
                        <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border rounded-md shadow-sm">
                            <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Work Style & Preferences{openSections.workStyle ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                            <CollapsibleContent className="p-4 pt-2 space-y-4">
                                <div><Label htmlFor="work_style_preference">I do my best work in...{isRequired('work_style_preference') && <span className="text-red-500 ml-1">*</span>}</Label>
                                    <Select name="work_style_preference" value={profile.work_style_preference ?? ''} onValueChange={(v) => handleChange('work_style_preference',v)}>
                                        <SelectTrigger><SelectValue placeholder="Select a work style..." /></SelectTrigger>
                                        <SelectContent>{workStyleOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div><Label htmlFor="conflict_resolution_style">When I disagree with a colleague, I prefer to...{isRequired('conflict_resolution_style') && <span className="text-red-500 ml-1">*</span>}</Label>
                                    <Select name="conflict_resolution_style" value={profile.conflict_resolution_style ?? ''} onValueChange={(v) => handleChange('conflict_resolution_style',v)}>
                                        <SelectTrigger><SelectValue placeholder="Select a conflict style..." /></SelectTrigger>
                                        <SelectContent>{conflictResolutionOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div><Label htmlFor="communication_preference">I communicate most effectively through...{isRequired('communication_preference') && <span className="text-red-500 ml-1">*</span>}</Label>
                                    <Select name="communication_preference" value={profile.communication_preference ?? ''} onValueChange={(v) => handleChange('communication_preference',v)}>
                                        <SelectTrigger><SelectValue placeholder="Select a communication style..." /></SelectTrigger>
                                        <SelectContent>{communicationPreferenceOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div><Label htmlFor="change_tolerance">I am most productive when...{isRequired('change_tolerance') && <span className="text-red-500 ml-1">*</span>}</Label>
                                    <Select name="change_tolerance" value={profile.change_tolerance ?? ''} onValueChange={(v) => handleChange('change_tolerance',v)}>
                                        <SelectTrigger><SelectValue placeholder="Select your preference for change..." /></SelectTrigger>
                                        <SelectContent>{changeToleranceOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                            </CollapsibleContent>
                        </Collapsible>

                        {/* Contact & Basic Information Section */}
                        <Collapsible open={openSections.personalInfo} onOpenChange={() => toggleSection('personalInfo')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Contact & Basic Information{openSections.personalInfo ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                            <CollapsibleContent className="p-4 pt-0 space-y-4">
                                <div><Label htmlFor="full_name">Full Name</Label><Input id="full_name" type="text" value={profile.full_name || ''} onChange={(e) => handleChange('full_name', e.target.value)} /></div>
                                <div><Label htmlFor="location">Current Location</Label><div className="flex items-center space-x-2"><Input id="location" type="text" value={profile.location || ''} onChange={(e) => handleChange('location', e.target.value)} placeholder="e.g., San Francisco, CA" className="flex-grow"/><Button type="button" onClick={handleGetLocation} disabled={isLocationLoading} variant="outline" size="icon" aria-label="Use my current location"><MapPin className="h-4 w-4" /></Button>{(profile.latitude && profile.longitude) && (<Button type="button" onClick={handleClearLocation} variant="ghost" size="icon" aria-label="Clear location"><XCircle className="h-4 w-4 text-red-500" /></Button>)}</div>
                                {(profile.latitude != null && profile.longitude != null) && <p className="text-xs text-gray-500 mt-1">Lat: {Number(profile.latitude).toFixed(4)}, Lon: {Number(profile.longitude).toFixed(4)}</p>}
                                </div>
                                <div><Label htmlFor="linkedin_url">LinkedIn Profile URL</Label><Input id="linkedin_url" type="url" value={profile.linkedin_url || ''} onChange={(e) => handleChange('linkedin_url', e.target.value)} placeholder="https://www.linkedin.com/in/yourprofile/" /></div>
                                <div><Label htmlFor="portfolio_url">Portfolio/Website URL</Label><Input id="portfolio_url" type="url" value={profile.portfolio_url || ''} onChange={(e) => handleChange('portfolio_url', e.target.value)} placeholder="https://your-portfolio.com" /></div>
                            </CollapsibleContent>
                        </Collapsible>

                        {/* Career Aspirations Section */}
                        <Collapsible open={openSections.careerGoals} onOpenChange={() => toggleSection('careerGoals')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Career Aspirations{openSections.careerGoals ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                            <CollapsibleContent className="p-4 pt-0 space-y-4">
                                <div><Label htmlFor="career_goals">Career Goals{isRequired('career_goals') && <span className="text-red-500 ml-1">*</span>}</Label><Textarea id="career_goals" value={profile.career_goals || ''} onChange={(e) => handleChange('career_goals', e.target.value)} rows={3} /></div>
                                <div><Label htmlFor="desired_job_titles">Desired Job Title(s){isRequired('desired_job_titles') && <span className="text-red-500 ml-1">*</span>}</Label><Input id="desired_job_titles" type="text" value={profile.desired_job_titles || ''} onChange={(e) => handleChange('desired_job_titles', e.target.value)} placeholder="e.g., Senior Product Manager, VP of Engineering" /></div>
                                <div><Label htmlFor="desired_salary_min">Desired Minimum Annual Salary</Label><Input id="desired_salary_min" type="text" inputMode="numeric" value={formatNumberForDisplay(profile.desired_salary_min)} onChange={(e) => handleChange('desired_salary_min', e.target.value)} placeholder="e.g., 150,000" /></div>
                                <div><Label htmlFor="desired_salary_max">Desired Maximum Annual Salary</Label><Input id="desired_salary_max" type="text" inputMode="numeric" value={formatNumberForDisplay(profile.desired_salary_max)} onChange={(e) => handleChange('desired_salary_max', e.target.value)} placeholder="e.g., 180,000" /></div>
                                <div><Label htmlFor="target_industries">Target Industries</Label><Input id="target_industries" type="text" value={profile.target_industries || ''} onChange={(e) => handleChange('target_industries', e.target.value)} /></div>
                            </CollapsibleContent>
                        </Collapsible>
                        
                        {/* Work Environment & Requirements Section */}
                         <Collapsible open={openSections.workEnv} onOpenChange={() => toggleSection('workEnv')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Work Environment & Requirements{openSections.workEnv ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                            <CollapsibleContent className="p-4 pt-0 space-y-4">
                                <div><Label htmlFor="preferred_work_style_select">Preferred Work Location</Label>
                                    <Select value={profile.preferred_work_style || 'NO_PREFERENCE'} onValueChange={(v) => handleChange('preferred_work_style', v)}>
                                        <SelectTrigger id="preferred_work_style_select"><SelectValue placeholder="Select a preference..." /></SelectTrigger>
                                        <SelectContent>{preferredWorkLocationOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                {profile.preferred_work_style === 'HYBRID' && (
                                    <div className="flex items-center space-x-2 pl-1 pt-2">
                                        <Checkbox id="is_remote_preferred" checked={!!profile.is_remote_preferred} onCheckedChange={(checked) => handleCheckboxChange('is_remote_preferred', !!checked)} />
                                        <Label htmlFor="is_remote_preferred" className="font-normal">I have a strong preference for the remote part of Hybrid.</Label>
                                    </div>
                                )}
                                <div><Label htmlFor="preferred_company_size">Preferred Company Size</Label>
                                    <Select value={profile.preferred_company_size ?? 'NO_PREFERENCE'} onValueChange={(value) => handleChange('preferred_company_size', value)}>
                                        <SelectTrigger><SelectValue placeholder="No Preference" /></SelectTrigger>
                                        <SelectContent>{companySizeOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div><Label htmlFor="skills">Skills</Label><Textarea id="skills" value={profile.skills || ''} onChange={(e) => handleChange('skills', e.target.value)} rows={3} /></div>
                            </CollapsibleContent>
                        </Collapsible>

                        {/* Personality Section */}
                        <Collapsible open={openSections.personality} onOpenChange={() => toggleSection('personality')} className="border rounded-md shadow-sm"><CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg">Personality & Self-Assessment{openSections.personality ? <ChevronUp/> : <ChevronDown/>}</CollapsibleTrigger>
                            <CollapsibleContent className="p-4 pt-0 space-y-4">
                                <div><Label htmlFor="personality_16_personalities">16 Personalities (e.g., INTJ)</Label><Input id="personality_16_personalities" type="text" value={profile.personality_16_personalities || ''} onChange={(e) => handleChange('personality_16_personalities', e.target.value)} /></div>
                                <div><Label htmlFor="disc_assessment">DISC Assessment</Label><Input id="disc_assessment" type="text" value={profile.disc_assessment || ''} onChange={(e) => handleChange('disc_assessment', e.target.value)} placeholder="e.g., D, I/D, etc." /></div>
                                <div><Label htmlFor="clifton_strengths">Top 5 CliftonStrengths</Label><Textarea id="clifton_strengths" value={profile.clifton_strengths || ''} onChange={(e) => handleChange('clifton_strengths', e.target.value)} rows={2} placeholder="e.g., Achiever, Learner, Strategic, etc." /></div>
                                <div><Label htmlFor="other_personal_attributes">Other Personal Attributes</Label><Textarea id="other_personal_attributes" value={profile.other_personal_attributes || ''} onChange={(e) => handleChange('other_personal_attributes', e.target.value)} rows={3} /></div>
                            </CollapsibleContent>
                        </Collapsible>

                        {/* Save/Nav Buttons */}
                        <div className="pt-4 space-y-2">
                            <div className="flex items-center justify-end space-x-4">
                                <Link href="/dashboard" passHref><Button variant="outline">Back to Dashboard</Button></Link>
                                <Button type="submit" disabled={isSaving} className="bg-indigo-600 hover:bg-indigo-700">{isSaving ? 'Saving...' : 'Save Profile'}</Button>
                            </div>
                            <div className="h-6 mt-2 text-right">
                                {error && <div className="text-red-600" role="alert">{error}</div>}
                                {successMessage && <div className="text-green-600" role="alert">{successMessage}</div>}
                            </div>
                        </div>
                    </form>
                </div>

                <div className="mt-8">
                    <ResumeUploadForm />
                </div>
            </div>
        </main>
    );
}