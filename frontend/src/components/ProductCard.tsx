'use client';

import { motion } from 'framer-motion';
import { Package, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Product } from '@/lib/api';

interface ProductCardProps {
  product: Product;
  rank: number;
  index: number;
}

export function ProductCard({ product, rank, index }: ProductCardProps) {
  const [showDebug, setShowDebug] = useState(false);
  const similarityPercent = (product.similarity * 100).toFixed(1);
  
  const getColorAccent = (color: string) => {
    const colorMap: Record<string, { bg: string; border: string }> = {
      red: { bg: 'bg-red-500/10', border: 'border-red-500/30' },
      blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
      green: { bg: 'bg-green-500/10', border: 'border-green-500/30' },
      black: { bg: 'bg-gray-900/20', border: 'border-gray-500/30' },
      white: { bg: 'bg-gray-100', border: 'border-gray-300' },
      multicolor: { bg: 'bg-gradient-to-br from-red-500/10 via-yellow-500/10 to-blue-500/10', border: 'border-purple-500/30' },
    };
    return colorMap[color.toLowerCase()] || { bg: 'bg-gray-100 dark:bg-gray-800', border: 'border-gray-300 dark:border-gray-700' };
  };

  const colorStyle = getColorAccent(product.color);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="group relative"
    >
      {/* Decorative Corners */}
      <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-transparent group-hover:border-black dark:group-hover:border-white transition-colors duration-300" />
      <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-transparent group-hover:border-black dark:group-hover:border-white transition-colors duration-300" />
      <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-transparent group-hover:border-black dark:group-hover:border-white transition-colors duration-300" />
      <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-transparent group-hover:border-black dark:group-hover:border-white transition-colors duration-300" />

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 overflow-hidden card-hover">
        {/* Product Visual */}
        <div className={`relative h-44 ${colorStyle.bg} flex items-center justify-center`}>
          {/* Rank Badge */}
          <div className="absolute top-3 left-3 bg-black dark:bg-white text-white dark:text-black px-2 py-1 font-mono text-xs tracking-wider">
            #{rank}
          </div>
          
          {/* Similarity Score */}
          <div className="absolute top-3 right-3 border border-black dark:border-white px-2 py-1 font-mono text-xs bg-white/80 dark:bg-black/80 backdrop-blur-sm">
            {similarityPercent}%
          </div>
          
          {/* Product Icon */}
          <div className="relative">
            <Package className="w-12 h-12 text-gray-400" />
            <div className="absolute inset-0 glitch-overlay" />
          </div>

          {/* Scanline Effect */}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/5 to-transparent" 
                 style={{ backgroundSize: '100% 4px' }} />
          </div>
        </div>

        {/* Product Info */}
        <div className="p-4 space-y-3">
          <h3 className="font-semibold text-sm tracking-wide line-clamp-1 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
            {product.title.toUpperCase()}
          </h3>
          
          <p className="text-gray-500 dark:text-gray-400 text-xs line-clamp-2 font-mono leading-relaxed">
            {product.description}
          </p>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 pt-2">
            <span className={`px-2 py-1 text-xs font-mono tracking-wider border ${colorStyle.border}`}>
              {product.category}
            </span>
            <span className={`px-2 py-1 text-xs font-mono tracking-wider border ${colorStyle.border}`}>
              {product.color}
            </span>
          </div>

          {/* Debug Scores */}
          {product.debug_scores && (
            <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
              <button
                onClick={() => setShowDebug(!showDebug)}
                className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors font-mono tracking-wider"
              >
                {showDebug ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                DEBUG DATA
              </button>
              {showDebug && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-2 p-2 bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800"
                >
                  {Object.entries(product.debug_scores).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs font-mono py-1">
                      <span className="text-gray-500">{key}</span>
                      <span className="text-gray-700 dark:text-gray-300">
                        {typeof value === 'number' ? value.toFixed(4) : String(value)}
                      </span>
                    </div>
                  ))}
                </motion.div>
              )}
            </div>
          )}

          {/* Product ID */}
          <div className="pt-2 text-xs text-gray-400 font-mono tracking-wider">
            ID: {product.product_id.slice(0, 12)}...
          </div>
        </div>
      </div>
    </motion.div>
  );
}

interface ProductGridProps {
  products: Product[];
  isLoading?: boolean;
}

export function ProductGrid({ products, isLoading }: ProductGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.05 }}
            className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 overflow-hidden"
          >
            <div className="h-44 bg-gray-100 dark:bg-gray-800 animate-pulse" />
            <div className="p-4 space-y-3">
              <div className="h-4 bg-gray-100 dark:bg-gray-800 animate-pulse w-3/4" />
              <div className="h-3 bg-gray-100 dark:bg-gray-800 animate-pulse" />
              <div className="h-3 bg-gray-100 dark:bg-gray-800 animate-pulse w-5/6" />
              <div className="flex gap-2 pt-2">
                <div className="h-6 w-16 bg-gray-100 dark:bg-gray-800 animate-pulse" />
                <div className="h-6 w-12 bg-gray-100 dark:bg-gray-800 animate-pulse" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
      >
        <div className="relative inline-block mb-6">
          <div className="w-20 h-20 border-2 border-gray-300 dark:border-gray-700 flex items-center justify-center">
            <Package className="w-8 h-8 text-gray-400" />
          </div>
          <div className="absolute -top-2 -left-2 w-4 h-4 border-t-2 border-l-2 border-black dark:border-white" />
          <div className="absolute -bottom-2 -right-2 w-4 h-4 border-b-2 border-r-2 border-black dark:border-white" />
        </div>
        <h3 className="font-orbitron text-xl font-bold mb-2">NO RESULTS FOUND</h3>
        <p className="text-gray-500 dark:text-gray-400 font-mono text-sm">
          Try adjusting your search query or filters
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
    >
      {products.map((product, index) => (
        <ProductCard 
          key={product.product_id} 
          product={product} 
          rank={index + 1}
          index={index}
        />
      ))}
    </motion.div>
  );
}
