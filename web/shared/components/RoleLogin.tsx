import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import toast from 'react-hot-toast';
import { Lock, User } from 'lucide-react';

interface RoleOption {
  role: 'manager' | 'marketing' | 'direction' | 'admin';
  label: string;
  email: string;
  password: string;
  description: string;
  color: string;
}

const ROLE_OPTIONS: RoleOption[] = [
  {
    role: 'manager',
    label: 'Manager',
    email: 'laurent@pharma.com',
    password: 'Laurent2024!',
    description: 'Gestion des délégués et territoires',
    color: 'bg-blue-600',
  },
  {
    role: 'marketing',
    label: 'Marketing',
    email: 'sophie@pharma.com',
    password: 'Sophie2024!',
    description: 'Segmentation et campagnes',
    color: 'bg-purple-600',
  },
  {
    role: 'direction',
    label: 'Direction',
    email: 'pierre@pharma.com',
    password: 'Pierre2024!',
    description: 'Tableau de bord exécutif',
    color: 'bg-red-600',
  },
];

export const RoleLogin: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [selectedRole, setSelectedRole] = useState<RoleOption | null>(null);
  const [customEmail, setCustomEmail] = useState('');
  const [customPassword, setCustomPassword] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const [error, setError] = useState('');

  const handleRoleLogin = async (role: RoleOption) => {
    setError('');
    try {
      await login(role.email, role.password);
      toast.success(`Connecté en tant que ${role.label}`);
      navigate('/dashboard');
    } catch (err: any) {
      const message = err?.message || err?.response?.data?.detail || 'Identifiants invalides';
      setError(message);
      toast.error(message);
    }
  };

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(customEmail, customPassword);
      toast.success('Connexion réussie');
      navigate('/dashboard');
    } catch (err: any) {
      const message = err?.message || err?.response?.data?.detail || 'Identifiants invalides';
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center px-4">
      <div className="w-full max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl mb-6 shadow-lg">
            <Lock className="text-white" size={32} />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">CRM Pharma Pro</h1>
          <p className="text-gray-400 text-lg">Système de gestion intégré multi-rôles</p>
        </div>

        {!useCustom ? (
          <>
            {/* Role Selection Grid */}
            <div className="grid md:grid-cols-3 gap-4 mb-8">
              {ROLE_OPTIONS.map((role) => (
                <button
                  key={role.role}
                  onClick={() => handleRoleLogin(role)}
                  disabled={isLoading}
                  className="group relative overflow-hidden rounded-xl bg-gray-800 border border-gray-700 hover:border-gray-600 transition-all duration-300 p-6 text-left hover:shadow-xl hover:shadow-blue-500/10"
                >
                  {/* Background gradient on hover */}
                  <div
                    className={`absolute inset-0 ${role.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
                  ></div>

                  <div className="relative z-10">
                    <div className="flex items-center mb-4">
                      <div className={`${role.color} p-3 rounded-lg group-hover:shadow-lg group-hover:shadow-${role.color}/50 transition-all`}>
                        <User size={24} className="text-white" />
                      </div>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{role.label}</h3>
                    <p className="text-gray-400 text-sm mb-4">{role.description}</p>

                    {/* Credentials preview */}
                    <div className="bg-gray-900 rounded-lg p-3 mb-4">
                      <p className="text-xs text-gray-500">Email: <span className="text-gray-300">{role.email}</span></p>
                      <p className="text-xs text-gray-500">Mot de passe: <span className="text-gray-300">••••••••</span></p>
                    </div>

                    <button
                      onClick={() => handleRoleLogin(role)}
                      disabled={isLoading}
                      className={`w-full ${role.color} text-white font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition-all`}
                    >
                      {isLoading ? 'Connexion...' : 'Se connecter'}
                    </button>
                  </div>
                </button>
              ))}
            </div>

            {/* Custom Login Link */}
            <div className="text-center">
              <button
                onClick={() => setUseCustom(true)}
                className="text-gray-400 hover:text-gray-300 text-sm transition-colors"
              >
                Ou utilisez d'autres identifiants
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Custom Login Form */}
            <form onSubmit={handleCustomLogin} className="max-w-md mx-auto bg-gray-800 border border-gray-700 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-6">Connexion personnalisée</h2>

              {error && (
                <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-sm text-red-400 mb-4">
                  {error}
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input
                  type="email"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="votre@email.com"
                  disabled={isLoading}
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">Mot de passe</label>
                <input
                  type="password"
                  value={customPassword}
                  onChange={(e) => setCustomPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || !customEmail || !customPassword}
                className="w-full px-4 py-2 bg-purple-600 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity mb-4"
              >
                {isLoading ? 'Connexion...' : 'Se connecter'}
              </button>

              <button
                type="button"
                onClick={() => setUseCustom(false)}
                className="w-full text-gray-400 hover:text-gray-300 text-sm transition-colors"
              >
                ← Retour aux rôles
              </button>
            </form>
          </>
        )}

        {/* Footer Info */}
        <div className="mt-12 grid md:grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
            <p className="text-gray-400 text-sm">Manager</p>
            <p className="text-white font-mono text-xs mt-2">laurent@pharma.com</p>
          </div>
          <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
            <p className="text-gray-400 text-sm">Marketing</p>
            <p className="text-white font-mono text-xs mt-2">sophie@pharma.com</p>
          </div>
          <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
            <p className="text-gray-400 text-sm">Direction</p>
            <p className="text-white font-mono text-xs mt-2">pierre@pharma.com</p>
          </div>
        </div>
      </div>
    </div>
  );
};
