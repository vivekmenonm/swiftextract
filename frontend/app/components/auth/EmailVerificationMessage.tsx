'use client';

import React from 'react';

interface EmailVerificationMessageProps {
  message: string;
  isLoading?: boolean;
  isError?: boolean;
}

const EmailVerificationMessage: React.FC<EmailVerificationMessageProps> = ({ message, isLoading, isError }) => {
  let messageColor = '#333'; // Default color
  if (isLoading) {
    messageColor = '#0070f3'; // Blue for loading
  } else if (isError) {
    messageColor = 'red'; // Red for error
  } else {
    messageColor = 'green'; // Green for success (assuming if not loading and not error, it's success)
  }

  return (
    <div style={{ textAlign: 'center', padding: '2rem', border: '1px solid #eee', borderRadius: '8px', maxWidth: '500px', margin: 'auto' }}>
      <h2>Email Verification</h2>
      {isLoading && <p style={{ fontSize: '1.1rem', color: messageColor }}>⏳ Verifying...</p>}
      <p style={{ fontSize: '1.1rem', color: messageColor }}>{message}</p>
      {!isLoading && isError && (
        <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          If you think this is an error, please try the link again or request a new verification email.
        </p>
      )}
      {!isLoading && !isError && message.includes("successfully verified") && (
         <a href="/login" style={{ marginTop: '1rem', display: 'inline-block', padding: '0.5rem 1rem', backgroundColor: '#0070f3', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
            Go to Login
          </a>
      )}
    </div>
  );
};

export default EmailVerificationMessage;
