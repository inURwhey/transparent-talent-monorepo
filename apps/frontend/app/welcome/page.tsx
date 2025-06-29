// Path: apps/frontend/app/welcome/page.tsx
'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

export default function WelcomePage() {
    const router = useRouter();
    const { getToken } = useAuth();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    const [resumeText, setResumeText] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = useCallback(async (event: React.FormEvent) => {
        event.preventDefault();
        if (!resumeText.trim() || isProcessing) return;

        setIsProcessing(true);
        setError(null);

        try {
            const token = await getToken();
            if (!token) throw new Error("Authentication failed. Please try logging in again.");

            const response = await fetch(`${apiBaseUrl}/api/onboarding/parse-resume`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ resume_text: resumeText }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process resume.');
            }

            // On success, redirect to the profile page for review and completion.
            router.push('/dashboard/profile');

        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsProcessing(false);
        }
    }, [resumeText, isProcessing, getToken, apiBaseUrl, router]);

    return (
        <main className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
            <div className="w-full max-w-2xl bg-white p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome to Transparent Talent</h1>
                <p className="text-gray-600 mb-6">Let's start by understanding your experience. Paste your full resume below to begin building your personalized career profile.</p>

                <form onSubmit={handleSubmit}>
                    <div className="space-y-2">
                        <Label htmlFor="resume-text" className="text-lg font-semibold">Your Resume</Label>
                        <Textarea
                            id="resume-text"
                            placeholder="Paste your full resume here..."
                            className="min-h-[400px] text-sm"
                            value={resumeText}
                            onChange={(e) => setResumeText(e.target.value)}
                            required
                        />
                    </div>
                    
                    {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

                    <Button type="submit" disabled={isProcessing} className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded text-lg">
                        {isProcessing ? 'Analyzing Your Experience...' : 'Create My Profile'}
                    </Button>
                </form>
            </div>
        </main>
    );
}