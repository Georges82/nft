import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [certificate, setCertificate] = useState(null);

  // Set up axios interceptor for automatic certificate inclusion
  useEffect(() => {
    const interceptor = axios.interceptors.request.use(
      (config) => {
        const storedCertificate = localStorage.getItem('joinery_certificate');
        if (storedCertificate && config.url.includes('/api/')) {
          config.headers.Authorization = `Bearer ${storedCertificate}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle auth errors
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(interceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Check for existing certificate on app load
  useEffect(() => {
    checkExistingAuth();
  }, []);

  const checkExistingAuth = async () => {
    try {
      const storedCertificate = localStorage.getItem('joinery_certificate');
      if (storedCertificate) {
        // Verify certificate is still valid
        const response = await axios.get(`${API}/auth/verify`, {
          headers: { Authorization: `Bearer ${storedCertificate}` }
        });
        
        if (response.data.valid) {
          setUser(response.data.user);
          setCertificate(storedCertificate);
        } else {
          localStorage.removeItem('joinery_certificate');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('joinery_certificate');
    } finally {
      setLoading(false);
    }
  };

  const login = async (certificateString) => {
    try {
      setLoading(true);
      
      // Validate certificate with backend
      const response = await axios.post(`${API}/auth/login`, {
        certificate: certificateString
      });

      if (response.data.user) {
        setUser(response.data.user);
        setCertificate(certificateString);
        localStorage.setItem('joinery_certificate', certificateString);
        return { success: true, user: response.data.user };
      }
      
      return { success: false, error: 'Invalid certificate' };
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || 'Authentication failed';
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setCertificate(null);
    localStorage.removeItem('joinery_certificate');
  };

  const isAuthenticated = () => {
    return user !== null && certificate !== null;
  };

  const value = {
    user,
    certificate,
    loading,
    login,
    logout,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};