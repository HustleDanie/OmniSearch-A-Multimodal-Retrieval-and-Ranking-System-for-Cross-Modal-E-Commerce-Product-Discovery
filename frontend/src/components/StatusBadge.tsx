'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
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
        setError('Offline');
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 border border-gray-300 dark:border-gray-700 text-xs font-mono tracking-wider">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Loader2 className="w-3 h-3 text-yellow-500" />
        </motion.div>
        <span className="text-gray-500">CONNECTING</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 border border-red-500/50 text-xs font-mono tracking-wider">
        <WifiOff className="w-3 h-3 text-red-500" />
        <span className="text-red-500">OFFLINE</span>
      </div>
    );
  }

  const isHealthy = health?.status === 'healthy';
  const isDemo = health?.mode === 'demo';

  return (
    <div className={`flex items-center gap-2 px-3 py-1 border text-xs font-mono tracking-wider ${
      isHealthy 
        ? 'border-green-500/50' 
        : 'border-yellow-500/50'
    }`}>
      <motion.div
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [1, 0.7, 1]
        }}
        transition={{ 
          duration: 2, 
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <Wifi className={`w-3 h-3 ${isHealthy ? 'text-green-500' : 'text-yellow-500'}`} />
      </motion.div>
      <span className={isHealthy ? 'text-green-500' : 'text-yellow-500'}>
        {isDemo ? 'DEMO' : health?.status?.toUpperCase()}
      </span>
    </div>
  );
}
