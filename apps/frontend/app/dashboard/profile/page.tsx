// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp, MapPin } from 'lucide-react'; // Added MapPin icon

// --- TYPE DEFINITIONS ---
// Updated Profile type to include latitude and longitude from the backend
interface Profile {
    id: number;
    user_id: number;
    full_name: string | null;
    current_location: string | null;
    latitude: number | null;
    longitude: number | null;
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
    preferred_work_style: 'On-site' | 'Remote' | 'Hybrid' | null;
    is_remote_preferred: boolean | null;
}

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
    const [isLocationLoading, setIsLocationLoading] = useState(false);

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

    useEffect(() => {
        const fetchProfile = async () => {
            if (!isUserLoaded || !isAuthLoaded) return;
            setIsLoading(true);
            setError(null);
            try {
                const response = await authedFetch(`${apiBaseUrl}/api/profile`);
                if (!response.ok) throw new Error('Failed to fetch profile.');
                const data: Profile = await response.json();
                setProfile(data);
            } catch (err: any) {
                setError(err.message || "An unexpected error occurred.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchProfile();
    }, [isUserLoaded, isAuthLoaded, apiBaseUrl, authedFetch]);

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

    const handleSubmit = useCallback(async (e: FormEvent) => {
        e.preventDefault();
        if (!profile || isSaving) return;
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            await authedFetch(`${apiBaseUrl}/api/profile`, {
                method: 'PUT',
                body: JSON.stringify(profile),
            });
            setSuccessMessage("Profile saved successfully!");
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err: any) {
            setError(err.message || "An unexpected error occurred while saving.");
        } finally {
            setIsSaving(false);
        }
    }, [profile, isSaving, apiBaseUrl, authedFetch]);

    // --- NEW: GEOLOCATION HANDLER ---
    const handleGetLocation = useCallback(() => {
        if (!navigator.geolocation) {
            setError("Geolocation is not supported by your browser.");
            return;
        }

        setIsLocationLoading(true);
        setError(null);

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                
                // Optimistically update the UI
                setProfile(prev => prev ? { ...prev, latitude, longitude } : null);

                // Save to the backend
                try {
                    await authedFetch(`${apiBaseUrl}/api/profile`, {
                        method: 'PUT',
                        body: JSON.stringify({ latitude, longitude }),
                    });
                    setSuccessMessage("Location updated successfully!");
                    setTimeout(() => setSuccessMessage(null), 3000);
                } catch (err: any) {
                    setError(err.message || "Failed to save location.");
                } finally {
                    setIsLocationLoading(false);
                }
            },
            (error) => {
                setError(`Geolocation error: ${error.message}`);
                setIsLocationLoading(false);
            }
        );
    }, [apiBaseUrl, authedFetch]);

    if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    if (error && !profile) return <div className="min-h-screen flex items-center justify-center text-center">...</div>;
    if (!profile) return null;

    return (
        <main className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold text-gray-800 mb-6">Your Profile</h1>

                {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">...</div>}
                {successMessage && <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4">...</div>}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <Collapsible open={isPersonalInfoOpen} onOpenChange={setIsPersonalInfoOpen} className="border rounded-md shadow-sm bg-gray-50">
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 font-semibold text-lg text-gray-700 hover:bg-gray-100">
                            Contact & Basic Information {isPersonalInfoOpen ? <ChevronUp /> : <ChevronDown />}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="p-4 bg-white space-y-4">
                            <div>
                                <Label htmlFor="full_name">Full Name</Label>
                                <Input id="full_name" type="text" value={profile.full_name || ''} onChange={(e) => handleChange('full_name', e.target.value)} />
                            </div>
                            
                            {/* --- NEW: Location section with Geolocation button --- */}
                            <div>
                                <Label htmlFor="current_location">Current Location</Label>
                                <div className="flex items-center space-x-2">
                                    <Input
                                        id="current_location"
                                        type="text"
                                        value={profile.current_location || ''}
                                        onChange={(e) => handleChange('current_location', e.target.value)}
                                        placeholder="e.g., San Francisco, CA"
                                        className="flex-grow"
                                    />
                                    <Button type="button" onClick={handleGetLocation} disabled={isLocationLoading} variant="outline" size="icon">
                                        <MapPin className="h-4 w-4" />
                                        <span className="sr-only">Use my current location</span>
                                    </Button>
                                </div>
                                {(profile.latitude && profile.longitude) && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        Lat: {profile.latitude.toFixed(4)}, Lon: {profile.longitude.toFixed(4)}
                                    </p>
                                )}
                            </div>

                            <div>
                                <Label htmlFor="linkedin_profile_url">LinkedIn Profile URL</Label>
                                <Input id="linkedin_profile_url" type="url" value={profile.linkedin_profile_url || ''} onChange={(e) => handleChange('linkedin_profile_url', e.target.value)} placeholder="https://www.linkedin.com/in/yourprofile/" />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                    
                    {/* ... (rest of the collapsible sections remain unchanged) ... */}
                    
                    <Collapsible open={isCareerGoalsOpen} onOpenChange={setIsCareerGoalsOpen} className="border rounded-md shadow-sm bg-gray-50">
                        {/* ... content ... */}
                    </Collapsible>
                    <Collapsible open={isWorkEnvOpen} onOpenChange={setIsWorkEnvOpen} className="border rounded-md shadow-sm bg-gray-50">
                        {/* ... content ... */}
                    </Collapsible>
                    <Collapsible open={isSkillsOpen} onOpenChange={setIsSkillsOpen} className="border rounded-md shadow-sm bg-gray-50">
                       {/* ... content ... */}
                    </Collapsible>
                    <Collapsible open={isPersonalityOpen} onOpenChange={setIsPersonalityOpen} className="border rounded-md shadow-sm bg-gray-50">
                        {/* ... content ... */}
                    </Collapsible>

                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded">
                        {isSaving ? 'Saving...' : 'Save Profile'}
                    </Button>
                </form>
            </div>
        </main>
    );
}