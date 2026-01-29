'use client';

import { Product } from '@/lib/api';

interface ProductCardProps {
  product: Product;
  rank: number;
}

export function ProductCard({ product, rank }: ProductCardProps) {
  const similarityPercent = (product.similarity * 100).toFixed(1);
  
  // Generate a placeholder image based on product color
  const getColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      red: 'bg-red-200',
      blue: 'bg-blue-200',
      green: 'bg-green-200',
      black: 'bg-gray-800',
      white: 'bg-gray-100',
      multicolor: 'bg-gradient-to-r from-red-200 via-yellow-200 to-blue-200',
    };
    return colorMap[color.toLowerCase()] || 'bg-gray-200';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Product Image / Placeholder */}
      <div className={`relative h-48 ${getColorClass(product.color)} flex items-center justify-center`}>
        <div className="absolute top-2 left-2 bg-white dark:bg-gray-900 px-2 py-1 rounded-full text-xs font-bold">
          #{rank}
        </div>
        <div className="absolute top-2 right-2 bg-blue-600 text-white px-2 py-1 rounded-full text-xs font-bold">
          {similarityPercent}% match
        </div>
        <span className="text-4xl opacity-50">👕</span>
      </div>

      {/* Product Info */}
      <div className="p-4 space-y-2">
        <h3 className="font-semibold text-lg text-gray-900 dark:text-white line-clamp-1">
          {product.title}
        </h3>
        
        <p className="text-gray-600 dark:text-gray-400 text-sm line-clamp-2">
          {product.description}
        </p>

        <div className="flex flex-wrap gap-2 pt-2">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
            📁 {product.category}
          </span>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
            🎨 {product.color}
          </span>
        </div>

        {/* Debug Scores (if available) */}
        {product.debug_scores && (
          <div className="pt-2 border-t dark:border-gray-700">
            <details className="text-xs text-gray-500">
              <summary className="cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                Debug Scores
              </summary>
              <div className="mt-2 space-y-1 bg-gray-50 dark:bg-gray-900 p-2 rounded">
                {Object.entries(product.debug_scores).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span>{key}:</span>
                    <span className="font-mono">{typeof value === 'number' ? value.toFixed(3) : String(value)}</span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {/* Product ID */}
        <div className="pt-2 text-xs text-gray-400">
          ID: {product.product_id}
        </div>
      </div>
    </div>
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
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden animate-pulse">
            <div className="h-48 bg-gray-200 dark:bg-gray-700" />
            <div className="p-4 space-y-3">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300">No products found</h3>
        <p className="text-gray-500 mt-2">Try a different search query or adjust your filters</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {products.map((product, index) => (
        <ProductCard key={product.product_id} product={product} rank={index + 1} />
      ))}
    </div>
  );
}
