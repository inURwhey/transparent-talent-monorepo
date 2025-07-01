// Path: apps/frontend/app/dashboard/profile/page.tsx
'use client';

import { useState, useEffect, useCallback, FormEvent } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation'; // Import useRouter
import Link from 'next/link';
// ... other imports

// ... (helpers and component definition)

export default function UserProfilePage() {
    const { getToken, isLoaded: isAuthLoaded } = useAuth();
    const router = useRouter(); // Initialize router
    // ... other state variables

    // ... fetchProfile, handleChange, etc.

    const updateProfileData = useCallback(async (payload: Partial<Omit<Profile, 'id' | 'user_id'>>) => {
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        console.log("Updating profile with payload:", payload);
        try {
            const response = await authedFetch(`${apiBaseUrl}/api/profile`, { method: 'PUT', body: JSON.stringify(payload) });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save profile.');
            
            const updatedProfile: Profile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully! Redirecting...");
            
            // Redirect to dashboard after a successful save to force data refresh
            setTimeout(() => {
                router.push('/dashboard');
            }, 1500); // Delay allows user to see success message

        } catch (err: any) { 
            console.error("Error updating profile:", err);
            setError(err.message); 
            setIsSaving(false); // Ensure saving is set to false on error
        } 
        // No finally block for setIsSaving(false) here, as we want it to stay true during redirect delay
    }, [apiBaseUrl, authedFetch, router]);
    
    // ... (rest of the component is unchanged)
}