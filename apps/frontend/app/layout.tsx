import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider, SignedIn, SignedOut, UserButton } from '@clerk/nextjs'
import Link from 'next/link';
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Transparent Talent",
  description: "Clarity in the job search process.",
};

function Header() {
  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem', borderBottom: '1px solid #ccc' }}>
      {/* Wrapped the h1 in a Link component */}
      <Link href="/" passHref>
        <h1>Transparent Talent</h1>
      </Link>
      <div>
        <SignedIn>
          {/* Mount the UserButton component */}
          <UserButton afterSignOutUrl="/"/>
        </SignedIn>
        <SignedOut>
          {/* Signed out users get sign in button */}
          <Link href="/sign-in">Sign In</Link>
        </SignedOut>
      </div>
    </header>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // The deprecated afterSignUpUrl prop has been removed. 
    // This is now correctly handled by the NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL environment variable.
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          <Header />
          <main>{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}