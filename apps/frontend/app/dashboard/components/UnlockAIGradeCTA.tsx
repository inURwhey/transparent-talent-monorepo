// Path: apps/frontend/app/dashboard/components/UnlockAIGradeCTA.tsx
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function UnlockAIGradeCTA() {
  return (
    <div className="text-center">
      <Link href="/dashboard/profile" passHref>
        <Button variant="link" className="p-0 h-auto text-xs text-blue-600">
          Unlock
        </Button>
      </Link>
      <p className="text-xs text-muted-foreground -mt-1">w/ Profile</p>
    </div>
  );
}