// apps/frontend/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

// Define all routes that should be publicly accessible.
// All other routes will be protected.
const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)', // Allow sign-in routes
  '/sign-up(.*)'  // Allow sign-up routes
]);

export default clerkMiddleware((auth, request) => {
  // If the route is not public, then protect it.
  // The `protect()` method will automatically redirect unauthenticated
  // users to the sign-in page.
  if (!isPublicRoute(request)) {
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