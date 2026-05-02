// ─── SessionContext.js — Delegate Session Management ──────────────────────────
import React, { createContext, useState } from 'react';
import { fetchAllRoles, BASE_URL } from '../api/client';

export const SessionContext = createContext();

// Sample delegates database (in real app, this comes from API)
const DELEGATES_DB = {
  541: {
    id_deleg: 541,
    nom: 'Delégué Pharma',
    region: 'Île-de-France',
    zone: 'Z2 - Paris Est',
    email: 'deleg.541@pharma.fr',
    phone: '+33 6 12 34 56 78',
    score: 84,
    tier: 'Excellent',
    percentile: 'Top 20%',
    territory: 'Nb05',
    color: '#34D399',
  },
  542: {
    id_deleg: 542,
    nom: 'Delégué Pro',
    region: 'Rhône-Alpes',
    zone: 'Z1 - Lyon',
    email: 'deleg.542@pharma.fr',
    phone: '+33 6 98 76 54 32',
    score: 79,
    tier: 'Very Good',
    percentile: 'Top 30%',
    territory: 'Nb05',
    color: '#4F8EF7',
  },
  543: {
    id_deleg: 543,
    nom: 'Delégué Expert',
    region: 'Provence-Alpes',
    zone: 'Z3 - Marseille',
    email: 'deleg.543@pharma.fr',
    phone: '+33 6 55 66 77 88',
    score: 72,
    tier: 'Good',
    percentile: 'Top 50%',
    territory: 'Nb05',
    color: '#A78BFA',
  },
};

export function SessionProvider({ children }) {
  const [delegates, setDelegates] = useState(DELEGATES_DB);
  const [currentDelegate, setCurrentDelegate] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const loginDelegate = (id_deleg) => {
    const delegate = delegates[id_deleg];
    if (!delegate) return false;

    setCurrentDelegate(delegate);
    setIsLoggedIn(true);

    // Enrich with API data in the background — never blocks login
    fetchAllRoles(id_deleg, 'delegate').then((raw) => {
      const perf = raw?.roles?.delegate?.delegate_scorecard || raw?.roles?.delegate?.performance;
      if (perf) {
        setCurrentDelegate(prev => ({
          ...prev,
          score: perf.ca_achievement_pct != null ? Math.round(perf.ca_achievement_pct) : prev.score,
          tier: perf.tier || prev.tier,
        }));
      }
    }).catch(() => {
      // API unavailable — keep local data, no crash
    });

    return true;
  };

  const logout = () => {
    setCurrentDelegate(null);
    setIsLoggedIn(false);
  };

  const getDelegateInfo = (id_deleg) => {
    return delegates[id_deleg] || null;
  };

  const value = {
    currentDelegate,
    isLoggedIn,
    delegates,
    loginDelegate,
    logout,
    getDelegateInfo,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}
