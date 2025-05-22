'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter
import Input from '../ui/Input';
import apiCall from '../../lib/api';

const LoginForm: React.FC = () => {
  const [login, setLogin] = useState(''); // Can be username or email
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const router = useRouter(); // Initialize useRouter

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!login) newErrors.login = 'Username or Email is required';
    if (!password) newErrors.password = 'Password is required';
    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccessMessage('');
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsLoading(true);

    const response = await apiCall<{ user?: { username?: string }; message?: string }>('/login', {
      method: 'POST',
      body: { login, password },
    });

    setIsLoading(false);

    if (response.error) {
      setErrors({ form: response.error || 'An unexpected error occurred.' });
      localStorage.removeItem('loggedInUser'); // Clear localStorage on error
    } else if (response.data && response.data.user && response.data.user.username) {
      setSuccessMessage(response.data.message || 'Login successful!');
      localStorage.setItem('loggedInUser', response.data.user.username); // Store username
      setPassword(''); // Clear password field
      
      // Redirect to homepage
      router.push('/'); 
    } else {
      // Handle cases where response.data or user or username might be missing
      setErrors({ form: 'Login failed: Invalid user data received.' });
      localStorage.removeItem('loggedInUser');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: 'auto', padding: '2rem', border: '1px solid #eee', borderRadius: '8px' }}>
      <h2>Login</h2>
      {successMessage && <p style={{ color: 'green', marginBottom: '1rem' }}>{successMessage}</p>}
      {errors.form && <p style={{ color: 'red', marginBottom: '1rem' }}>{errors.form}</p>}
      
      <Input
        label="Username or Email"
        name="login"
        type="text"
        value={login}
        onChange={(e) => setLogin(e.target.value)}
        error={errors.login}
        disabled={isLoading}
      />
      <Input
        label="Password"
        name="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading}
        style={{
          backgroundColor: isLoading ? '#ccc' : '#0070f3',
          color: 'white',
          padding: '0.75rem 1.5rem',
          border: 'none',
          borderRadius: '4px',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          fontSize: '1rem',
          width: '100%',
          marginTop: '1rem',
        }}
      >
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

export default LoginForm;
