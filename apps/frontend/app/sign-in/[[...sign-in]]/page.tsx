import { SignIn } from "@clerk/nextjs";

export default function Page() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <SignIn 
        routing="path"
        path="/sign-in"
        // The afterSignInUrl is read from the NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL env var by default.
        // We can specify a fallback here in case the env var is not set.
        fallbackRedirectUrl="/dashboard"
      />
    </div>
  );
}