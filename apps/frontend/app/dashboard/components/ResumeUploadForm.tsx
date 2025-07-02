// Path: apps/frontend/app/dashboard/components/ResumeUploadForm.tsx
'use client';

import { useState, FormEvent, useCallback } from 'react';
import { useAuth } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal } from "lucide-react"

export function ResumeUploadForm() {
    const [resumeText, setResumeText] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const { getToken } = useAuth();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    const authedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Authentication token is missing.");
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        headers.set('Content-Type', 'application/json');
        return fetch(url, { ...options, headers });
    }, [getToken]);

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();
        if (!resumeText.trim() || isSubmitting) return;

        setIsSubmitting(true);
        setError(null);
        setSuccessMessage(null);

        try {
            const response = await authedFetch(`${apiBaseUrl}/api/onboarding/parse-resume`, {
                method: 'POST',
                body: JSON.stringify({ resume_text: resumeText }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to submit resume.');
            }
            
            setSuccessMessage('Resume submitted successfully! Your profile has been updated, and the page will now refresh to reflect any changes.');
            setResumeText('');

            setTimeout(() => {
                window.location.assign('/dashboard');
            }, 2500);

        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Update Your Resume</h2>
            <p className="text-sm text-gray-600 mb-4">
                Pasting a new resume will update your active resume on file and enrich any empty fields in your profile. Your existing, manually-entered data will not be overwritten.
            </p>
            {successMessage && (
                <Alert variant="default" className="mb-4 bg-green-50 border-green-300">
                    <Terminal className="h-4 w-4" />
                    <AlertTitle>Success!</AlertTitle>
                    <AlertDescription>{successMessage}</AlertDescription>
                </Alert>
            )}
            {error && (
                 <Alert variant="destructive" className="mb-4">
                    <Terminal className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}
            <form onSubmit={handleSubmit}>
                <Label htmlFor="resumeText" className="block text-sm font-medium text-gray-700">
                    Paste your full resume text
                </Label>
                <Textarea
                    id="resumeText"
                    name="resumeText"
                    rows={10}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Paste your resume here..."
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    required
                    minLength={100}
                />
                <Button
                    type="submit"
                    className="mt-4 w-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-indigo-300"
                    disabled={isSubmitting || !resumeText.trim()}
                >
                    {isSubmitting ? 'Processing...' : 'Submit New Resume'}
                </Button>
            </form>
        </div>
    );
}