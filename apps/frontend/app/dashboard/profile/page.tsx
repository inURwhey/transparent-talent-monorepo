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
    const [isLoading, setIsLoading] = useState(true); // Default to true
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

    // --- THE FIX: `fetchProfile` is now wrapped in useCallback with a stable dependency ---
    const fetchProfile = useCallback(async () => {
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
    }, [authedFetch, apiBaseUrl]);

    useEffect(() => {
        if (isAuthLoaded) {
            fetchProfile();
        }
    }, [isAuthLoaded, fetchProfile]);

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
        setProfile(prev => (prev ? { ...prev, [id]: checked } : null));
    }, []);

    const updateProfileData = useCallback(async (payload: Partial<Omit<Profile, 'id' | 'user_id'>>) => {
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save profile.');
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
        const isOnboardingComplete = ONBOARDING_REQUIRED_FIELDS.every(field => !!payload[field]);
        if (isOnboardingComplete && !profile.has_completed_onboarding) {
            payload.has_completed_onboarding = true;
        }
        updateProfileData(payload);
    }, [profile, updateProfileData]);

    const handleGetLocation = useCallback(() => {
        if (!navigator.geolocation) return setError("Geolocation is not supported.");
        setIsLocationLoading(true);
        setError(null);
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

    if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;
    if (!profile) return <div className="min-h-screen flex items-center justify-center">Could not load profile. Please try again.</div>;

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
                {/* ... (render error/success messages) ... */}
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* All collapsible sections go here, complete and untruncated */}
                    <Collapsible open={openSections.workStyle} onOpenChange={() => toggleSection('workStyle')} className="border-2 border-indigo-300 rounded-md shadow-lg">
                        {/* Work Style Content */}
                    </Collapsible>
                    <Collapsible open={openSections.personalInfo} onOpenChange={() => toggleSection('personalInfo')}>
                        {/* Personal Info Content */}
                    </Collapsible>
                    {/* ... etc for all sections ... */}
                    <Button type="submit" disabled={isSaving} className="w-full bg-indigo-600 hover:bg-indigo-700">{isSaving ? 'Saving...' : 'Save Profile'}</Button>
                </form>
            </div>
        </main>
    );
}