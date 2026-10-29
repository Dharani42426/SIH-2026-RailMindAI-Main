import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Activity } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        height: '100vh', width: '100vw',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: 'var(--color-bg-main)',
        flexDirection: 'column', gap: '24px'
      }}>
        <Activity size={40} color="var(--color-primary)" className="animate-spin" />
        <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-navy)', letterSpacing: '0.05em' }}>
          RESTORING SESSION...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
