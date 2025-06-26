import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicRoutes = /^(\/sign-in.*|\/sign-up.*)$/;

// The middleware function MUST be marked as 'async'
export async function middleware(request: NextRequest) {
  if (publicRoutes.test(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  // We MUST 'await' the result of the auth() call
  const { userId } = await auth();
  if (!userId) {
    const signInUrl = new URL('/sign-in', request.url);
    signInUrl.searchParams.set('redirect_url', request.url);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};