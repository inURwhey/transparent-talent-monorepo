// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation'; // CORRECTED: Removed '=>' from import
import { Button } from '@/components/ui/button';
import { Input }s from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
// --- SHADCN UI IMPORTS ---
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// NEW: Collapsible component imports
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp } from 'lucide-react'; // Icons for collapsible state

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
    preferred_work_style: 'On-site' | 'Remote' | 'Hybrid' | null; // Explicitly define union type for Select
    is_remote_preferred: boolean | null;
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

    // MODIFIED: State for collapsible sections - all set to true for default expanded
    const [isPersonalInfoOpen, setIsPersonalInfoOpen] = useState(true);
    const [isCareerGoalsOpen, setIsCareerGoalsOpen] = useState(true);
    const [isWorkEnvOpen, setIsWorkEnvOpen] = useState(true);
    const [isSkillsOpen, setIsSkillsOpen] = useState(true);
    const [isPersonalityOpen, setIsPersonalityOpen] = useState(true);


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

    // MODIFIED: Handle changes for all input types, including conditional logic for preferred_work_style
    // This now also handles values directly from Shadcn Select's onValueChange
    const handleChange = useCallback((id: keyof Profile, value: any) => {
        setProfile(prev => {
            if (!prev) return null;
            let updatedProfile = { ...prev };

            // Handle value for text/select fields: empty string means null
            // For selects, "null" string needs to be converted back to actual null
            const finalValue = value === '' || value === 'null' ? null : value;
            updatedProfile = { ...updatedProfile, [id]: finalValue };

            // NEW LOGIC: If preferred_work_style is set to 'On-site', force is_remote_preferred to false
            if (id === 'preferred_work_style') {
                if (finalValue === 'On-site') {
                    updatedProfile.is_remote_preferred = false;
                }
            }
            return updatedProfile;
        });
    }, []);

    // Handle checkbox changes (remains separate for clarity with onCheckedChange prop)
    const handleCheckboxChange = useCallback((id: keyof Profile, checked: boolean) => {
        setProfile(prev => {
            if (!prev) return null;
            return { ...prev, [id]: checked };
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
        delete (payload as any).id;
        delete (payload as any).user_id;
        delete (payload as any).resume_url;

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
            setProfile(updatedProfile);
            setSuccessMessage("Profile saved successfully!");
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

    if (error && !profile) {
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
    if (!profile) return null;

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
                    {/* Collapsible: Contact & Basic Information */}
                    <Collapsible
                        open={isPersonalInfoOpen}
                        onOpenChange={setIsPersonalInfoOpen}
                        className="border rounded-md shadow-sm bg-gray-50"
                    >
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200">
                            Contact & Basic Information
                            {isPersonalInfoOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            {/* Full Name */}
                            <div>
                                <Label htmlFor="full_name">Full Name</Label>
                                <Input
                                    id="full_name"
                                    type="text"
                                    value={profile.full_name || ''}
                                    onChange={(e) => handleChange('full_name', e.target.value)}
                                />
                            </div>
                            {/* Current Location */}
                            <div>
                                <Label htmlFor="current_location">Current Location</Label>
                                <Input
                                    id="current_location"
                                    type="text"
                                    value={profile.current_location || ''}
                                    onChange={(e) => handleChange('current_location', e.target.value)}
                                />
                            </div>
                            {/* LinkedIn Profile URL */}
                            <div>
                                <Label htmlFor="linkedin_profile_url">LinkedIn Profile URL</Label>
                                <Input
                                    id="linkedin_profile_url"
                                    type="url"
                                    value={profile.linkedin_profile_url || ''}
                                    onChange={(e) => handleChange('linkedin_profile_url', e.target.value)}
                                    placeholder="https://www.linkedin.com/in/yourprofile/"
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Collapsible: Career Aspirations */}
                    <Collapsible
                        open={isCareerGoalsOpen}
                        onOpenChange={setIsCareerGoalsOpen}
                        className="border rounded-md shadow-sm bg-gray-50"
                    >
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200">
                            Career Aspirations
                            {isCareerGoalsOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            {/* Short Term Career Goal */}
                            <div>
                                <Label htmlFor="short_term_career_goal">Short-Term Career Goal</Label>
                                <Textarea
                                    id="short_term_career_goal"
                                    value={profile.short_term_career_goal || ''}
                                    onChange={(e) => handleChange('short_term_career_goal', e.target.value)}
                                    rows={3}
                                />
                            </div>
                            {/* Long Term Career Goals */}
                            <div>
                                <Label htmlFor="long_term_career_goals">Long-Term Career Goals</Label>
                                <Textarea
                                    id="long_term_career_goals"
                                    value={profile.long_term_career_goals || ''}
                                    onChange={(e) => handleChange('long_term_career_goals', e.target.value)}
                                    rows={3}
                                />
                            </div>
                            {/* Desired Title */}
                            <div>
                                <Label htmlFor="desired_title">Desired Job Title</Label>
                                <Input
                                    id="desired_title"
                                    type="text"
                                    value={profile.desired_title || ''}
                                    onChange={(e) => handleChange('desired_title', e.target.value)}
                                />
                            </div>
                            {/* Desired Annual Compensation */}
                            <div>
                                <Label htmlFor="desired_annual_compensation">Desired Annual Compensation</Label>
                                <Input
                                    id="desired_annual_compensation"
                                    type="text"
                                    value={profile.desired_annual_compensation || ''}
                                    onChange={(e) => handleChange('desired_annual_compensation', e.target.value)}
                                    placeholder="$150,000 - $180,000"
                                />
                            </div>
                            {/* Ideal Role Description */}
                            <div>
                                <Label htmlFor="ideal_role_description">Ideal Role Description</Label>
                                <Textarea
                                    id="ideal_role_description"
                                    value={profile.ideal_role_description || ''}
                                    onChange={(e) => handleChange('ideal_role_description', e.target.value)}
                                    rows={5}
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Collapsible: Work Environment & Requirements */}
                    <Collapsible
                        open={isWorkEnvOpen}
                        onOpenChange={setIsWorkEnvOpen}
                        className="border rounded-md shadow-sm bg-gray-50"
                    >
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200">
                            Work Environment & Requirements
                            {isWorkEnvOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            {/* Preferred Work Style (Using Shadcn Select) */}
                            <div>
                                <Label htmlFor="preferred_work_style">Preferred Work Style</Label>
                                <Select
                                    value={profile.preferred_work_style || 'null'}
                                    onValueChange={(value) => handleChange('preferred_work_style', value)}
                                >
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="No Preference" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="null">No Preference</SelectItem>
                                        <SelectItem value="On-site">On-site</SelectItem>
                                        <SelectItem value="Remote">Remote</SelectItem>
                                        <SelectItem value="Hybrid">Hybrid</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Is Remote Preferred (Using Shadcn Checkbox) - CONDITIONAL RENDERING */}
                            {profile.preferred_work_style !== 'On-site' && (
                                <div className="flex items-center space-x-2">
                                    <Checkbox
                                        id="is_remote_preferred"
                                        checked={profile.is_remote_preferred || false}
                                        onCheckedChange={(checked: boolean) => handleCheckboxChange('is_remote_preferred', checked)}
                                    />
                                    <Label
                                        htmlFor="is_remote_preferred"
                                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                    >
                                        I prefer remote work generally.
                                    </Label>
                                </div>
                            )}

                            {/* Preferred Company Size (Using Shadcn Select) */}
                            <div>
                                <Label htmlFor="preferred_company_size">Preferred Company Size</Label>
                                <Select
                                    value={profile.preferred_company_size || 'null'}
                                    onValueChange={(value) => handleChange('preferred_company_size', value)}
                                >
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="No Preference" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="null">No Preference</SelectItem>
                                        <SelectItem value="Startup (1-50 employees)">Startup (1-50 employees)</SelectItem>
                                        <SelectItem value="Small (51-200 employees)">Small (51-200 employees)</SelectItem>
                                        <SelectItem value="Medium (201-1000 employees)">Medium (201-1000 employees)</SelectItem>
                                        <SelectItem value="Large (1001-10000 employees)">Large (1001-10000 employees)</SelectItem>
                                        <SelectItem value="Enterprise (10000+ employees)">Enterprise (10000+ employees)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Ideal Work Culture */}
                            <div>
                                <Label htmlFor="ideal_work_culture">Ideal Work Culture (e.g., "Collaborative", "Autonomous", "Fast-paced")</Label>
                                <Textarea
                                    id="ideal_work_culture"
                                    value={profile.ideal_work_culture || ''}
                                    onChange={(e) => handleChange('ideal_work_culture', e.target.value)}
                                    rows={3}
                                />
                            </div>

                            {/* Disliked Work Culture */}
                            <div>
                                <Label htmlFor="disliked_work_culture">Disliked Work Culture</Label>
                                <Textarea
                                    id="disliked_work_culture"
                                    value={profile.disliked_work_culture || ''}
                                    onChange={(e) => handleChange('disliked_work_culture', e.target.value)}
                                    rows={3}
                                />
                            </div>

                            {/* Non-Negotiable Requirements */}
                            <div>
                                <Label htmlFor="non_negotiable_requirements">Non-Negotiable Requirements</Label>
                                <Textarea
                                    id="non_negotiable_requirements"
                                    value={profile.non_negotiable_requirements || ''}
                                    onChange={(e) => handleChange('non_negotiable_requirements', e.target.value)}
                                    rows={3}
                                />
                            </div>

                            {/* Deal Breakers */}
                            <div>
                                <Label htmlFor="deal_breakers">Deal Breakers (e.g., "On-call rotation", "Strictly in-office")</Label>
                                <Textarea
                                    id="deal_breakers"
                                    value={profile.deal_breakers || ''}
                                    onChange={(e) => handleChange('deal_breakers', e.target.value)}
                                    rows={3}
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Collapsible: Skills & Industry Focus */}
                    <Collapsible
                        open={isSkillsOpen}
                        onOpenChange={setIsSkillsOpen}
                        className="border rounded-md shadow-sm bg-gray-50"
                    >
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200">
                            Skills & Industry Focus
                            {isSkillsOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            {/* Core Strengths */}
                            <div>
                                <Label htmlFor="core_strengths">Core Strengths (comma-separated)</Label>
                                <Textarea
                                    id="core_strengths"
                                    value={profile.core_strengths || ''}
                                    onChange={(e) => handleChange('core_strengths', e.target.value)}
                                    rows={3}
                                />
                            </div>
                            {/* Skills to Avoid */}
                            <div>
                                <Label htmlFor="skills_to_avoid">Skills / Technologies to Avoid (comma-separated)</Label>
                                <Textarea
                                    id="skills_to_avoid"
                                    value={profile.skills_to_avoid || ''}
                                    onChange={(e) => handleChange('skills_to_avoid', e.target.value)}
                                    rows={3}
                                />
                            </div>
                            {/* Preferred Industries */}
                            <div>
                                <Label htmlFor="preferred_industries">Preferred Industries (comma-separated)</Label>
                                <Textarea
                                    id="preferred_industries"
                                    value={profile.preferred_industries || ''}
                                    onChange={(e) => handleChange('preferred_industries', e.target.value)}
                                    rows={2}
                                />
                            </div>
                            {/* Industries to Avoid */}
                            <div>
                                <Label htmlFor="industries_to_avoid">Industries to Avoid (comma-separated)</Label>
                                <Textarea
                                    id="industries_to_avoid"
                                    value={profile.industries_to_avoid || ''}
                                    onChange={(e) => handleChange('industries_to_avoid', e.target.value)}
                                    rows={2}
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Collapsible: Personality & Self-Assessment */}
                    <Collapsible
                        open={isPersonalityOpen}
                        onOpenChange={setIsPersonalityOpen}
                        className="border rounded-md shadow-sm bg-gray-50"
                    >
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200">
                            Personality & Self-Assessment
                            {isPersonalityOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            {/* Personality Adjectives */}
                            <div>
                                <Label htmlFor="personality_adjectives">Personality Adjectives (e.g., "Curious", "Analytical", "Adaptable")</Label>
                                <Textarea
                                    id="personality_adjectives"
                                    value={profile.personality_adjectives || ''}
                                    onChange={(e) => handleChange('personality_adjectives', e.target.value)}
                                    rows={2}
                                />
                            </div>
                            {/* Personality 16 Personalities */}
                            <div>
                                <Label htmlFor="personality_16_personalities">16 Personalities Type</Label>
                                <Input
                                    id="personality_16_personalities"
                                    type="text"
                                    value={profile.personality_16_personalities || ''}
                                    onChange={(e) => handleChange('personality_16_personalities', e.target.value)}
                                    placeholder="e.g., INTJ-T"
                                />
                            </div>
                            {/* Personality DISC */}
                            <div>
                                <Label htmlFor="personality_disc">DISC Profile</Label>
                                <Input
                                    id="personality_disc"
                                    type="text"
                                    value={profile.personality_disc || ''}
                                    onChange={(e) => handleChange('personality_disc', e.target.value)}
                                    placeholder="e.g., D-I"
                                />
                            </div>
                            {/* Personality Gallup Strengths */}
                            <div>
                                <Label htmlFor="personality_gallup_strengths">Gallup Strengths (comma-separated)</Label>
                                <Textarea
                                    id="personality_gallup_strengths"
                                    value={profile.personality_gallup_strengths || ''}
                                    onChange={(e) => handleChange('personality_gallup_strengths', e.target.value)}
                                    rows={2}
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>

                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded">
                        {isSaving ? 'Saving...' : 'Save Profile'}
                    </Button>
                </form>
            </div>
        </main>
    );
}