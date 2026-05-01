import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import toast from 'react-hot-toast';
import { Lock } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = React.useState('marketing@crmpharm.com');
  const [password, setPassword] = React.useState('password');
  const [error, setError] = React.useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      toast.success('Connexion réussie');
      navigate('/roi');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Identifiants invalides';
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-marketing rounded-lg mb-4">
            <Lock className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">CRM Pharma Marketing</h1>
          <p className="text-gray-400">Optimisation des campagnes</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red/15 border border-red/30 rounded-lg text-sm text-red">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-s1 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-marketing"
              placeholder="votre@email.com"
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Mot de passe
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-s1 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-marketing"
              placeholder="••••••••"
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-2 bg-marketing text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {isLoading ? 'Connexion...' : 'Connexion'}
          </button>
        </form>

        {/* Demo info */}
        <div className="mt-6 p-4 bg-s1 border border-bd rounded-lg text-xs text-gray-400">
          <p className="font-semibold text-gray-300 mb-2">Demo:</p>
          <p>Email: marketing@crmpharm.com</p>
          <p>Password: password</p>
        </div>
      </div>
    </div>
  );
};
