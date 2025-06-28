// apps/frontend/app/page.tsx

'use client'; // This directive is necessary for using client-side hooks like useAuth
import { useAuth } from '@clerk/nextjs';

import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="bg-gray-50 min-h-screen flex flex-col">
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="bg-white py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
                Replace Job Market Chaos with Career Clarity
              </h1>
              <p className="mt-6 text-lg leading-8 text-gray-600">
                Transparent Talent is a systematic, AI-powered framework to help you stop guessing and start making data-driven career decisions.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6"> 
                {/* Conditional rendering based on authentication status */}
                <AuthAwareGetStartedButton />
                <Link href="/dashboard" className="text-sm font-semibold leading-6 text-gray-900"> 
                  Go to Dashboard <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Problem Section */}
        <section className="bg-gray-50 py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl lg:text-center">
              <h2 className="text-base font-semibold leading-7 text-indigo-600">The Broken Talent Market</h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                The Job Search is Inefficient and Opaque
              </p>
              <p className="mt-6 text-lg leading-8 text-gray-600">
                Today's job market harms both seekers and employers with overwhelming noise on job boards, opaque matching algorithms, information asymmetry, and subjective bias in hiring decisions. This results in wasted time, poor experiences, and suboptimal outcomes.
              </p>
            </div>
          </div>
        </section>

        {/* Solution Section */}
        <section className="overflow-hidden bg-white py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 sm:gap-y-20 lg:mx-0 lg:max-w-none lg:grid-cols-2">
              <div className="lg:pr-8 lg:pt-4">
                <div className="lg:max-w-lg">
                  <h2 className="text-base font-semibold leading-7 text-indigo-600">Our Solution</h2>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">A Framework for Transparency</p>
                  <p className="mt-6 text-lg leading-8 text-gray-600">
                    We replace subjective, keyword-driven hiring with an explicit, multi-dimensional relevance calculation. Our system empowers you with the tools to systematically evaluate opportunities.
                  </p>
                  <dl className="mt-10 max-w-xl space-y-8 text-base leading-7 text-gray-600 lg:max-w-none">
                    <div className="relative pl-9">
                      <dt className="inline font-semibold text-gray-900">
                        AI-Powered Scoring.
                      </dt>
                      <dd className="inline"> Evaluate jobs against your unique profile, scoring for both Position Relevance and Environment Fit.</dd>
                    </div>
                    <div className="relative pl-9">
                      <dt className="inline font-semibold text-gray-900">
                        Dynamic Feedback Loop.
                      </dt>
                      <dd className="inline"> Your feedback on matches continuously refines the system's understanding of your nuanced preferences.</dd>
                    </div>
                    <div className="relative pl-9">
                      <dt className="inline font-semibold text-gray-900">
                        Proactive Anomaly Detection.
                      </dt>
                      <dd className="inline"> The platform identifies inconsistencies between your stated goals and actions, creating opportunities for strategic realignment.</dd>
                    </div>
                  </dl>
                </div>
              </div>
              {/* You can add an image or illustration here if you have one */}
              <div className="flex items-center justify-center p-8 bg-gray-100 rounded-lg">
                 <p className="text-gray-400 italic">Illustration or screenshot placeholder</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-white">
        <div className="mx-auto max-w-7xl overflow-hidden px-6 py-12 lg:px-8">
          <p className="text-center text-xs leading-5 text-gray-500">
            © {new Date().getFullYear()} Transparent Talent. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

// New component to handle conditional "Get Started" button logic
function AuthAwareGetStartedButton() {
  const { isSignedIn, isLoaded } = useAuth();

  if (!isLoaded) {
    // Show a placeholder or nothing while auth state is loading
    return (
      <div className="rounded-md bg-indigo-300 px-3.5 py-2.5 text-sm font-semibold text-white cursor-not-allowed">
        Loading...
      </div>
    );
  }

  if (isSignedIn) {
    // If signed in, "Get Started" button should navigate to the dashboard
    return (
      <Link
        href="/dashboard"
        className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
      >
        Go to Dashboard
      </Link>
    );
  }

  // If not signed in, "Get Started" button should navigate to sign-up
  return (
    <Link
      href="/sign-up"
      className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
    >
      Get Started
    </Link>
  );
}