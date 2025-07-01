// Path: apps/frontend/app/dashboard/components/CompleteProfileCTA.tsx
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function CompleteProfileCTA() {
  return (
    <div className="text-center p-6 bg-gray-50 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800">Get Personalized Recommendations</h3>
      <p className="mt-2 text-sm text-gray-600">
        Complete your profile to unlock AI-powered job recommendations tailored just for you. The more we know, the better your matches will be!
      </p>
      <Link href="/dashboard/profile" passHref>
        <Button className="mt-4">Complete Your Profile</Button>
      </Link>
    </div>
  );
}