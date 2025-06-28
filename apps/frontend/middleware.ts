// apps/frontend/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

// Define the routes that should be publicly accessible.
// All other routes will be protected.
const isPublicRoute = createRouteMatcher([
  '/', // The landing page
  '/sign-in(.*)', // The sign-in pages
  '/sign-up(.*)', // The sign-up pages
]);

export default clerkMiddleware((auth, request) => {
  // If the requested route is not in our list of public routes,
  // then it is a protected route and we need to enforce authentication.
  if (!isPublicRoute(request)) {
    // The 'auth' object passed to the middleware has the .protect() method.
    // This is the correct syntax.
    auth.protect();
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