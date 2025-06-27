import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const { isAuthenticated, token } = useAuth();
    const [isChecking, setIsChecking] = useState<boolean>(true);

    useEffect(() => {
        // We're already not authenticated, no need to check
        if (!token) {
            setIsChecking(false);
            return;
        }
        
        // Already authenticated from previous validation, no need to check again
        if (isAuthenticated) {
            setIsChecking(false);
        }
        
        // Otherwise, let's assume we're authenticated for now
        // to prevent immediate navigation flicker
        setIsChecking(false);
    }, [isAuthenticated, token]);

    if (isChecking) {
        // Show loading state while checking authentication
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    return <>{children}</>;
}; 