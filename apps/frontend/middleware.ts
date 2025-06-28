// apps/frontend/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

// This function defines which routes are protected.
// All routes are protected by default, except for the public-facing pages.
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)', // Protect the main dashboard
  '/user-profile(.*)', // Protect the user profile pages if they exist
  '/settings(.*)', // Protect settings pages
  // Add any other routes here that need to be behind authentication
]);

export default clerkMiddleware((auth, req) => {
  // If the requested route is a protected route, then enforce authentication.
  if (isProtectedRoute(req)) {
    auth().protect();
  }
});

export const config = {
  // This matcher ensures the middleware runs on all routes except for
  // internal Next.js routes and static assets.
  matcher: [
    '/((?!.*\\..*|_next).*)',
    '/',
    '/(api|trpc)(.*)',
  ],
};