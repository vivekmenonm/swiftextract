'use client'; // Required for hooks like useSearchParams and useEffect

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import EmailVerificationMessage from '../components/auth/EmailVerificationMessage';

const VerifyEmailContent: React.FC = () => {
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("Verifying your email... Please wait.");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);

  useEffect(() => {
    const verificationToken = searchParams.get('token');
    setToken(verificationToken);

    if (verificationToken) {
      setIsLoading(true);
      setIsError(false);
      setStatusMessage("Verifying your email...");

      // Simulate API call
      setTimeout(() => {
        // This is where the actual API call would go.
        // For now, we'll simulate success.
        // To simulate an error, you could change the condition below.
        // For example: if (verificationToken === 'invalid-token')
        if (verificationToken) { // Simulate success if any token is present
          setStatusMessage("Email successfully verified! You can now log in.");
          setIsLoading(false);
          setIsError(false);
        } else { // This else branch is for a simulated failed API call based on token content
          setStatusMessage("Invalid or expired token. Please try again.");
          setIsLoading(false);
          setIsError(true);
        }
      }, 2000);
    } else {
      setStatusMessage("No verification token found. Please check the link or request a new one.");
      setIsLoading(false);
      setIsError(true);
    }
  }, [searchParams]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#f0f2f5', padding: '1rem' }}>
      <EmailVerificationMessage message={statusMessage} isError={isError} isLoading={isLoading} />
    </div>
  );
};


// Next.js App Router requires that components using useSearchParams are wrapped in <Suspense>
// if they are rendered on the server side initially.
const VerifyEmailPage: React.FC = () => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
};

export default VerifyEmailPage;
