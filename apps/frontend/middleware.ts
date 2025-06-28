// apps/frontend/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

// Define the routes that should be publicly accessible.
// In this case, only the landing page at the root ('/') is public.
const isPublicRoute = createRouteMatcher(['/']);

// The main middleware function.
// It protects all routes by default.
export default clerkMiddleware((auth, req) => {
  // If the route is not public, then protect it.
  // The `protect()` method will automatically redirect unauthenticated
  // users to the sign-in page.
  if (!isPublicRoute(req)) {
    auth().protect();
  }
});

export const config = {
  // This matcher ensures that the middleware runs on all routes
  // except for internal Next.js routes (_next) and static assets (files with extensions).
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};