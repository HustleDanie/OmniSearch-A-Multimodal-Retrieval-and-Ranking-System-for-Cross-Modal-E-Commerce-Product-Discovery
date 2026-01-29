'use client';

import { useState, useEffect } from 'react';
import { checkHealth, HealthResponse } from '@/lib/api';

export function StatusBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError('API Offline');
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-sm">
        <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
        <span className="text-gray-600 dark:text-gray-400">Connecting...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 rounded-full text-sm">
        <div className="w-2 h-2 bg-red-500 rounded-full" />
        <span className="text-red-600 dark:text-red-400">{error}</span>
      </div>
    );
  }

  const isHealthy = health?.status === 'healthy';
  const isDemo = health?.mode === 'demo';

  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
      isHealthy 
        ? 'bg-green-100 dark:bg-green-900/30' 
        : 'bg-yellow-100 dark:bg-yellow-900/30'
    }`}>
      <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-yellow-500'}`} />
      <span className={isHealthy ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}>
        {isDemo ? 'Demo Mode' : health?.status}
      </span>
    </div>
  );
}
