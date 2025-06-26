import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define your public routes using a regular expression
const publicRoutes = /^(\/sign-in.*|\/sign-up.*)$/;

export function middleware(request: NextRequest) {
  // Check if the route is public
  if (publicRoutes.test(request.nextUrl.pathname)) {
    // If it's a public route, do nothing and let the request go through
    return NextResponse.next();
  }

  // For any non-public route, run Clerk's authentication
  const { userId } = auth();
  if (!userId) {
    // If no user is signed in, redirect them to the sign-in page
    const signInUrl = new URL('/sign-in', request.url);
    signInUrl.searchParams.set('redirect_url', request.url);
    return NextResponse.redirect(signInUrl);
  }

  // If the user is signed in, allow the request to proceed
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};