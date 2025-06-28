// apps/frontend/middleware.ts

import { authMiddleware } from "@clerk/nextjs";

export default authMiddleware({
  // The publicRoutes array specifies routes that are accessible to everyone,
  // including logged-out users.
  publicRoutes: ["/"],

  // The afterAuth function is called after authentication is complete.
  // Here, we can specify where to redirect users after they log in.
  afterAuth(auth, req, evt) {
    // For this example, we'll just let the middleware handle redirects.
    // A common use case is redirecting to a specific dashboard page:
    // if (auth.userId && !auth.isPublicRoute) {
    //   const dashboard = new URL('/dashboard', req.url)
    //   return NextResponse.redirect(dashboard)
    // }
  },
});

export const config = {
  // This matcher ensures that the middleware runs on all routes
  // except for internal Next.js routes and static assets.
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};