'use client';

import { useState } from 'react';
import { SearchBar, SearchOptions } from '@/components/SearchBar';
import { ProductGrid } from '@/components/ProductCard';
import { StatusBadge } from '@/components/StatusBadge';
import { 
  Product, 
  searchByText, 
  searchByImage, 
  searchMultimodal 
} from '@/lib/api';

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSearch, setLastSearch] = useState<{
    query: string;
    type: string;
    count: number;
    time: number;
  } | null>(null);

  const handleSearch = async (query: string, file: File | null, options: SearchOptions) => {
    setIsLoading(true);
    setError(null);
    const startTime = Date.now();

    try {
      const searchOptions = {
        top_k: options.top_k,
        category: options.category === 'All' ? undefined : options.category,
        color: options.color === 'All' ? undefined : options.color,
      };

      let results: Product[];
      let searchType: string;

      if (file && query) {
        // Multimodal search
        const response = await searchMultimodal({
          text: query,
          file,
          ...searchOptions,
          image_weight: options.imageWeight,
          text_weight: options.textWeight,
        });
        results = response.results;
        searchType = 'Multimodal';
      } else if (file) {
        // Image search
        const response = await searchByImage(file, searchOptions);
        results = response.results;
        searchType = 'Image';
      } else {
        // Text search
        const response = await searchByText(query, searchOptions);
        results = response.results;
        searchType = 'Text';
      }

      setProducts(results);
      setLastSearch({
        query: query || (file ? file.name : ''),
        type: searchType,
        count: results.length,
        time: Date.now() - startTime,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                🔍 OmniSearch
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Multimodal Product Discovery
              </p>
            </div>
            <StatusBadge />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Search Section */}
        <section className="mb-8">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </section>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">Error: {error}</span>
            </div>
            <p className="text-sm text-red-500 dark:text-red-300 mt-1">
              Make sure the API server is running (python demo_server.py)
            </p>
          </div>
        )}

        {/* Search Stats */}
        {lastSearch && !error && (
          <div className="mb-6 flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                lastSearch.type === 'Multimodal' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' :
                lastSearch.type === 'Image' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
              }`}>
                {lastSearch.type}
              </span>
            </span>
            <span>
              Found <strong>{lastSearch.count}</strong> products
            </span>
            <span>
              for &ldquo;{lastSearch.query}&rdquo;
            </span>
            <span className="text-gray-400">
              ({lastSearch.time}ms)
            </span>
          </div>
        )}

        {/* Results */}
        <section>
          {(products.length > 0 || isLoading) ? (
            <ProductGrid products={products} isLoading={isLoading} />
          ) : !lastSearch ? (
            /* Welcome State */
            <div className="text-center py-16">
              <div className="text-8xl mb-6">🛍️</div>
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
                Welcome to OmniSearch
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-8">
                Search for products using text, images, or both! Try searching for 
                &ldquo;red summer dress&rdquo; or upload an image to find similar products.
              </p>
              
              {/* Quick Search Examples */}
              <div className="flex flex-wrap justify-center gap-2">
                {['red dress', 'blue jeans', 'white sneakers', 'black jacket'].map((term) => (
                  <button
                    key={term}
                    onClick={() => handleSearch(term, null, {
                      top_k: 10,
                      category: 'All',
                      color: 'All',
                      searchType: 'text',
                      imageWeight: 0.6,
                      textWeight: 0.4,
                    })}
                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              OmniSearch: A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery
            </p>
            <div className="flex gap-4 text-sm">
              <a href="http://localhost:8000/docs" target="_blank" className="text-blue-600 hover:underline">
                API Docs
              </a>
              <a href="https://github.com/HustleDanie/OmniSearch-A-Multimodal-Retrieval-and-Ranking-System-for-Cross-Modal-E-Commerce-Product-Discovery" target="_blank" className="text-blue-600 hover:underline">
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
