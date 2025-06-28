// apps/frontend/middleware.ts

import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

// Define the route for the public landing page.
const isPublicRoute = createRouteMatcher(['/']);

// The default export is the Clerk middleware handler.
export default clerkMiddleware((auth, req) => {
  // If the route is not public, then it requires authentication.
  // The `protect()` method will handle redirection automatically.
  if (!isPublicRoute(req)) {
    auth().protect();
  }
});

export const config = {
  // This matcher ensures the middleware runs on all routes except for
  // internal Next.js routes and static assets.
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};