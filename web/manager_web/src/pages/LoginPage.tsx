import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import toast from 'react-hot-toast';
import { Lock } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('laurent@pharma.com');
  const [password, setPassword] = useState('Laurent2024!');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      toast.success('Connexion réussie');
      navigate('/dashboard');
    } catch (err: any) {
      const message = err?.message || err?.response?.data?.detail || 'Identifiants invalides';
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-purple rounded-lg mb-4">
            <Lock className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">CRM Pharma Manager</h1>
          <p className="text-gray-400">Tableau de bord responsable</p>
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
              className="w-full px-4 py-2 bg-s1 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple"
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
              className="w-full px-4 py-2 bg-s1 border border-bd rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple"
              placeholder="••••••••"
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-2 bg-purple text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {isLoading ? 'Connexion...' : 'Connexion'}
          </button>
        </form>

        {/* Demo info */}
        <div className="mt-6 p-4 bg-s1 border border-bd rounded-lg text-xs text-gray-400">
          <p className="font-semibold text-gray-300 mb-3">Test Accounts:</p>
          
          <div className="space-y-2 mb-3 pb-3 border-b border-bd">
            <p className="text-gray-300 font-medium">Manager</p>
            <p>Email: <span className="text-blue">laurent@pharma.com</span></p>
            <p>Password: <span className="text-blue">Laurent2024!</span></p>
          </div>

          <div className="space-y-2 mb-3 pb-3 border-b border-bd">
            <p className="text-gray-300 font-medium">Marketing</p>
            <p>Email: <span className="text-blue">sophie@pharma.com</span></p>
            <p>Password: <span className="text-blue">Sophie2024!</span></p>
          </div>

          <div className="space-y-2">
            <p className="text-gray-300 font-medium">Direction</p>
            <p>Email: <span className="text-blue">pierre@pharma.com</span></p>
            <p>Password: <span className="text-blue">Pierre2024!</span></p>
          </div>
        </div>
      </div>
    </div>
  );
};
