import React, { useState } from 'react';
import { useAuth } from '../lib/auth';
import { LogOut } from 'lucide-react';

interface LoginPageProps {}

export const LoginPage: React.FC<LoginPageProps> = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const demoLogins = [
    { role: 'Manager', email: 'manager@crmpharm.com' },
    { role: 'Marketing', email: 'marketing@crmpharm.com' },
    { role: 'Direction', email: 'direction@crmpharm.com' },
  ];

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">CRM Pharma</h1>
          <p className="text-gray-400">Unified Dashboard</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="bg-s1 border border-bd rounded-lg p-6 mb-6">
          {error && (
            <div className="mb-4 p-3 bg-red/20 border border-red/50 rounded text-red text-sm">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-300 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="manager@crmpharm.com"
              className="w-full px-4 py-2 bg-s2 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue transition-colors"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="password"
              className="w-full px-4 py-2 bg-s2 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue transition-colors"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Connexion...' : 'Connexion'}
          </button>
        </form>

        {/* Demo Accounts */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Demo Credentials (Password: password)</h3>
          <div className="space-y-3">
            {demoLogins.map(login => (
              <button
                key={login.email}
                onClick={() => {
                  setEmail(login.email);
                  setPassword('password');
                }}
                className="w-full p-3 bg-s2 hover:bg-s3 border border-bd rounded-lg text-left transition-colors"
              >
                <div className="font-semibold text-gray-100">{login.role}</div>
                <div className="text-xs text-gray-400">{login.email}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
