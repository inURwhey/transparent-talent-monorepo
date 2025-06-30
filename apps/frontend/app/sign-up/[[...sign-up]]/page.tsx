// Path: apps/frontend/app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from "@clerk/nextjs";

export default function Page() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <SignUp 
        routing="path" 
        path="/sign-up"
        // The afterSignUpUrl is read from the NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL env var by default.
        // We can specify a fallback here in case the env var is not set.
        fallbackRedirectUrl="/welcome"
      />
    </div>
  );
}