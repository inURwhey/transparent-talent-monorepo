import { SignedIn, SignedOut, UserButton, SignInButton } from "@clerk/nextjs";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          Transparent Talent
        </h1>
        <p className="mt-6 text-lg leading-8 text-gray-600">
          The frontend is deployed successfully. This is the application's public-facing root page.
        </p>

        <div className="mt-10 flex items-center justify-center gap-x-6">
          <SignedIn>
            <Link
              href="/dashboard"
              className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Go to Dashboard
            </Link>
            <div className="flex items-center gap-x-2">
              <span className="text-sm font-semibold text-gray-700">Account:</span>
              <UserButton afterSignOutUrl="/" />
            </div>
          </SignedIn>

          <SignedOut>
            {/* --- THE FIX IS HERE: Removed invalid 'afterSignInUrl' prop --- */}
            <div className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                <SignInButton mode="modal" />
            </div>
            <Link
              href="/sign-up"
              className="text-sm font-semibold leading-6 text-gray-900"
            >
              Sign Up <span aria-hidden="true">→</span>
            </Link>
          </SignedOut>
        </div>
      </div>
    </div>
  );
}