import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  preferred_language: string;
}

interface OAuthProvider {
  name: string;
  display_name: string;
  icon: string;
  color: string;
}

interface AuthContextType {
  user: User | null;
  sessionToken: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string, preferredLanguage?: string) => Promise<boolean>;
  loginWithOAuth: (provider: string, preferredLanguage?: string) => void;
  getOAuthProviders: () => Promise<OAuthProvider[]>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on app load
    const token = localStorage.getItem('sessionToken');
    if (token) {
      setSessionToken(token);
      // Verify token with backend
      verifySession(token);
    } else {
      setLoading(false);
    }

    // Handle OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const oauthToken = urlParams.get('token');
    const oauthSuccess = urlParams.get('success');
    const oauthError = urlParams.get('error');

    if (oauthToken && oauthSuccess === 'true') {
      setSessionToken(oauthToken);
      localStorage.setItem('sessionToken', oauthToken);
      verifySession(oauthToken);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (oauthError) {
      console.error('OAuth error:', oauthError);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const verifySession = async (token: string) => {
    try {
      const response = await fetch('/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        // Invalid token, clear it
        localStorage.removeItem('sessionToken');
        setSessionToken(null);
      }
    } catch (error) {
      console.error('Session verification failed:', error);
      localStorage.removeItem('sessionToken');
      setSessionToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      
      if (data.success) {
        setUser(data.user);
        setSessionToken(data.session_token);
        localStorage.setItem('sessionToken', data.session_token);
        return true;
      } else {
        console.error('Login failed:', data.error);
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const register = async (username: string, email: string, password: string, preferredLanguage: string = 'en'): Promise<boolean> => {
    try {
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username, 
          email, 
          password, 
          preferred_language: preferredLanguage 
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setUser(data.user);
        setSessionToken(data.session_token);
        localStorage.setItem('sessionToken', data.session_token);
        return true;
      } else {
        console.error('Registration failed:', data.error);
        return false;
      }
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  };

  const loginWithOAuth = (provider: string, preferredLanguage: string = 'en') => {
    // Redirect to OAuth provider
    window.location.href = `/auth/oauth/${provider}?language=${preferredLanguage}`;
  };

  const getOAuthProviders = async (): Promise<OAuthProvider[]> => {
    try {
      const response = await fetch('/auth/oauth/providers');
      const data = await response.json();
      
      if (data.success) {
        return data.providers;
      }
      return [];
    } catch (error) {
      console.error('Failed to get OAuth providers:', error);
      return [];
    }
  };

  const logout = () => {
    if (sessionToken) {
      // Call logout endpoint
      fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionToken}`
        }
      }).catch(console.error);
    }
    
    setUser(null);
    setSessionToken(null);
    localStorage.removeItem('sessionToken');
  };

  const value: AuthContextType = {
    user,
    sessionToken,
    login,
    register,
    loginWithOAuth,
    getOAuthProviders,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
