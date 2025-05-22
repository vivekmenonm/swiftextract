'use client';

import React, { useState } from 'react';
import Input from '../ui/Input';
import apiCall from '../../lib/api'; // Assuming api.ts is in a lib folder at the root of app

const RegisterForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!username) newErrors.username = 'Username is required';
    if (!email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(email)) newErrors.email = 'Email is invalid';
    if (!password) newErrors.password = 'Password is required';
    else if (password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    if (!confirmPassword) newErrors.confirmPassword = 'Confirm Password is required';
    else if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
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

    const response = await apiCall('/register', {
      method: 'POST',
      body: { username, email, password },
    });

    setIsLoading(false);

    if (response.error) {
      if (response.status === 400 && response.error) {
        // Assuming backend sends error messages in a specific format, e.g., { "message": "...", "errors": { "field": "message" } }
        // For now, displaying a generic error or specific messages if available
        if (typeof response.error === 'string') {
            setErrors({ form: response.error });
        } else if (typeof response.error === 'object' && (response.error as any).message) {
            setErrors({ form: (response.error as any).message });
        } else {
            setErrors({ form: 'Registration failed. Please try again.' });
        }
      } else {
        setErrors({ form: response.error || 'An unexpected error occurred.' });
      }
    } else if (response.data) {
      setSuccessMessage(response.data.message || 'Registration successful! Please check your email for verification.');
      // Optionally clear the form
      setUsername('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: 'auto', padding: '2rem', border: '1px solid #eee', borderRadius: '8px' }}>
      <h2>Register</h2>
      {successMessage && <p style={{ color: 'green', marginBottom: '1rem' }}>{successMessage}</p>}
      {errors.form && <p style={{ color: 'red', marginBottom: '1rem' }}>{errors.form}</p>}
      
      <Input
        label="Username"
        name="username"
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        error={errors.username}
        disabled={isLoading}
      />
      <Input
        label="Email"
        name="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
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
      <Input
        label="Confirm Password"
        name="confirmPassword"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        error={errors.confirmPassword}
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
        {isLoading ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
};

export default RegisterForm;
