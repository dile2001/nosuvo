import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [oauthProviders, setOauthProviders] = useState<any[]>([]);

  const { login, register, loginWithOAuth, getOAuthProviders } = useAuth();

  useEffect(() => {
    if (isOpen) {
      loadOAuthProviders();
    }
  }, [isOpen]);

  const loadOAuthProviders = async () => {
    try {
      const providers = await getOAuthProviders();
      setOauthProviders(providers);
    } catch (error) {
      console.error('Failed to load OAuth providers:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let success = false;
      
      if (isLogin) {
        success = await login(username, password);
      } else {
        if (!email.trim()) {
          setError('Email is required for registration');
          setLoading(false);
          return;
        }
        success = await register(username, email, password, preferredLanguage);
      }

      if (success) {
        onClose();
        setUsername('');
        setEmail('');
        setPassword('');
        setPreferredLanguage('en');
      } else {
        setError(isLogin ? 'Invalid username or password' : 'Registration failed. Username or email may already exist.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setUsername('');
    setEmail('');
    setPassword('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {isLogin ? 'Login' : 'Create Account'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="your@email.com"
                required={!isLogin}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Choose a username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter your password"
              required
              minLength={6}
            />
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Language
              </label>
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="pt">Portuguese</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese (Simplified)</option>
                <option value="zh-tw">Chinese (Traditional)</option>
                <option value="vi">Vietnamese</option>
              </select>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Create Account')}
          </button>
        </form>

        {/* OAuth Providers */}
        {oauthProviders.length > 0 && (
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-3">
              {oauthProviders.map((provider) => (
                <button
                  key={provider.name}
                  onClick={() => loginWithOAuth(provider.name, preferredLanguage)}
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 transition"
                  style={{ borderColor: provider.color }}
                >
                  <span className="mr-2">{provider.icon}</span>
                  {provider.display_name}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 text-center">
          <button
            onClick={switchMode}
            className="text-indigo-600 hover:text-indigo-800 text-sm"
          >
            {isLogin 
              ? "Don't have an account? Sign up" 
              : "Already have an account? Login"
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
