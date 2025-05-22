import React from 'react';
import ChangePasswordForm from '../components/auth/ChangePasswordForm';

const ChangePasswordPage: React.FC = () => {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#f0f2f5' }}>
      <ChangePasswordForm />
    </div>
  );
};

export default ChangePasswordPage;
