'use client';

import React, { useState } from 'react';
import Input from '../ui/Input';
import apiCall from '../../lib/api';

const ChangePasswordForm: React.FC = () => {
  const [username, setUsername] = useState(''); // Added username field
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!username) newErrors.username = 'Username is required'; // Validation for username
    if (!currentPassword) newErrors.currentPassword = 'Current Password is required';
    if (!newPassword) newErrors.newPassword = 'New Password is required';
    else if (newPassword.length < 6) newErrors.newPassword = 'New Password must be at least 6 characters';
    if (!confirmNewPassword) newErrors.confirmNewPassword = 'Confirm New Password is required';
    else if (newPassword !== confirmNewPassword) newErrors.confirmNewPassword = 'New passwords do not match';
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

    const response = await apiCall('/change_password', {
      method: 'POST',
      body: { username, current_password: currentPassword, new_password: newPassword, confirm_password: confirmNewPassword },
    });

    setIsLoading(false);

    if (response.error) {
      setErrors({ form: response.error || 'An unexpected error occurred.' });
    } else if (response.data) {
      setSuccessMessage(response.data.message || 'Password changed successfully!');
      // Optionally clear the form
      setUsername('');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: 'auto', padding: '2rem', border: '1px solid #eee', borderRadius: '8px' }}>
      <h2>Change Password</h2>
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
        label="Current Password"
        name="currentPassword"
        type="password"
        value={currentPassword}
        onChange={(e) => setCurrentPassword(e.target.value)}
        error={errors.currentPassword}
        disabled={isLoading}
      />
      <Input
        label="New Password"
        name="newPassword"
        type="password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        error={errors.newPassword}
        disabled={isLoading}
      />
      <Input
        label="Confirm New Password"
        name="confirmNewPassword"
        type="password"
        value={confirmNewPassword}
        onChange={(e) => setConfirmNewPassword(e.target.value)}
        error={errors.confirmNewPassword}
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
        {isLoading ? 'Changing Password...' : 'Change Password'}
      </button>
    </form>
  );
};

export default ChangePasswordForm;
