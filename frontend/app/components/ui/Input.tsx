import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

const Input: React.FC<InputProps> = ({ label, name, error, ...rest }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label htmlFor={name} style={{ display: 'block', marginBottom: '0.5rem' }}>
        {label}
      </label>
      <input
        id={name}
        name={name}
        {...rest}
        style={{
          width: '100%',
          padding: '0.5rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          borderColor: error ? 'red' : '#ccc',
        }}
      />
      {error && <p style={{ color: 'red', fontSize: '0.8rem', marginTop: '0.25rem' }}>{error}</p>}
    </div>
  );
};

export default Input;
