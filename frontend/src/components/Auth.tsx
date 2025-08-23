import React, { useState } from 'react';
import { apiService } from '../services/api';
import type { User } from '../services/api';

export const Auth: React.FC<{ onAuthSuccess: (user: User | null) => void }> = ({
  onAuthSuccess,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiService.login({
        username_or_email: usernameOrEmail,
        password,
      });
      onAuthSuccess(res.user || null);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload = { email, username, password };
      await apiService.register(payload);
      // After registering, try logging in automatically
      const loginRes = await apiService.login({
        username_or_email: username,
        password,
      });
      onAuthSuccess(loginRes.user || null);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
      <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">
          {mode === 'login' ? 'Sign in' : 'Create account'}
        </h2>

        {error && <div className="text-sm text-red-400 mb-3">{error}</div>}

        {mode === 'login' ? (
          <form onSubmit={handleLogin}>
            <label className="block text-sm text-gray-300 mb-1">
              Email or username
            </label>
            <input
              value={usernameOrEmail}
              onChange={(e) => setUsernameOrEmail(e.target.value)}
              className="w-full mb-3 px-3 py-2 rounded bg-gray-800 border border-gray-700"
            />
            <label className="block text-sm text-gray-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mb-4 px-3 py-2 rounded bg-gray-800 border border-gray-700"
            />
            <div className="flex items-center justify-between">
              <button
                disabled={loading}
                className="bg-green-600 px-4 py-2 rounded"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
              <button
                type="button"
                onClick={() => setMode('register')}
                className="text-sm text-gray-400 underline"
              >
                Create account
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <label className="block text-sm text-gray-300 mb-1">Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mb-3 px-3 py-2 rounded bg-gray-800 border border-gray-700"
            />
            <label className="block text-sm text-gray-300 mb-1">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full mb-3 px-3 py-2 rounded bg-gray-800 border border-gray-700"
            />
            <label className="block text-sm text-gray-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mb-4 px-3 py-2 rounded bg-gray-800 border border-gray-700"
            />
            <div className="flex items-center justify-between">
              <button
                disabled={loading}
                className="bg-green-600 px-4 py-2 rounded"
              >
                {loading ? 'Creating...' : 'Create account'}
              </button>
              <button
                type="button"
                onClick={() => setMode('login')}
                className="text-sm text-gray-400 underline"
              >
                Back to sign in
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default Auth;
