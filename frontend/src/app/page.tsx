'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Image, X, SlidersHorizontal, Sparkles } from 'lucide-react';
import { SearchBar, SearchOptions } from '@/components/SearchBar';
import { ProductGrid } from '@/components/ProductCard';
import { StatusBadge } from '@/components/StatusBadge';
import { ThemeToggle } from '@/components/ThemeToggle';
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
        const response = await searchByImage(file, searchOptions);
        results = response.results;
        searchType = 'Image';
      } else {
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
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="relative">
                <div className="w-10 h-10 border-2 border-black dark:border-white flex items-center justify-center">
                  <Search className="w-5 h-5" />
                </div>
                <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-black dark:border-white" />
                <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-black dark:border-white" />
              </div>
              <div>
                <h1 className="font-orbitron text-xl md:text-2xl font-bold tracking-wider">
                  OMNISEARCH
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400 tracking-widest uppercase">
                  Multimodal Discovery
                </p>
              </div>
            </motion.div>
            
            <div className="flex items-center gap-4">
              <StatusBadge />
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-12 md:py-20 overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px),
                              linear-gradient(to bottom, currentColor 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }} />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 md:px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="font-orbitron text-3xl md:text-5xl lg:text-6xl font-bold mb-4 tracking-tight">
              SEARCH REIMAGINED
            </h2>
            <div className="w-20 h-1 bg-black dark:bg-white mx-auto mb-6" />
            <p className="text-gray-600 dark:text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
              Harness the power of multimodal AI to discover products using 
              <span className="text-black dark:text-white font-semibold"> text</span>, 
              <span className="text-black dark:text-white font-semibold"> images</span>, or 
              <span className="text-black dark:text-white font-semibold"> both</span>.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 md:px-6 pb-16">
        {/* Search Section */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-12"
        >
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </motion.section>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-8 p-4 border border-red-500/50 bg-red-500/10 relative"
            >
              <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-red-500" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-red-500" />
              <div className="flex items-center gap-3">
                <X className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-semibold text-red-500">Error: {error}</p>
                  <p className="text-sm text-red-400 mt-1">
                    Make sure the API server is running (python demo_server.py)
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search Stats */}
        <AnimatePresence>
          {lastSearch && !error && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-8 flex flex-wrap items-center gap-4 text-sm font-mono"
            >
              <span className={`px-3 py-1 border ${
                lastSearch.type === 'Multimodal' 
                  ? 'border-purple-500 text-purple-500' 
                  : lastSearch.type === 'Image' 
                  ? 'border-green-500 text-green-500' 
                  : 'border-blue-500 text-blue-500'
              }`}>
                {lastSearch.type.toUpperCase()}
              </span>
              <span className="text-gray-500 dark:text-gray-400">
                Found <span className="text-black dark:text-white font-bold">{lastSearch.count}</span> results
              </span>
              <span className="text-gray-500 dark:text-gray-400">
                for &ldquo;<span className="text-black dark:text-white">{lastSearch.query}</span>&rdquo;
              </span>
              <span className="text-gray-400">
                [{lastSearch.time}ms]
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <section>
          {(products.length > 0 || isLoading) ? (
            <ProductGrid products={products} isLoading={isLoading} />
          ) : !lastSearch ? (
            /* Welcome State */
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-center py-16 md:py-24"
            >
              <div className="relative inline-block mb-8">
                <div className="w-24 h-24 border-2 border-gray-300 dark:border-gray-700 flex items-center justify-center">
                  <Sparkles className="w-10 h-10 text-gray-400" />
                </div>
                <div className="absolute -top-2 -left-2 w-6 h-6 border-t-2 border-l-2 border-black dark:border-white" />
                <div className="absolute -bottom-2 -right-2 w-6 h-6 border-b-2 border-r-2 border-black dark:border-white" />
              </div>
              
              <h3 className="font-orbitron text-2xl md:text-3xl font-bold mb-4">
                START YOUR SEARCH
              </h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-10">
                Enter a text query, upload an image, or combine both for 
                multimodal product discovery.
              </p>
              
              {/* Quick Search Examples */}
              <div className="flex flex-wrap justify-center gap-3">
                {['red dress', 'blue jeans', 'white sneakers', 'black jacket'].map((term) => (
                  <motion.button
                    key={term}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleSearch(term, null, {
                      top_k: 10,
                      category: 'All',
                      color: 'All',
                      searchType: 'text',
                      imageWeight: 0.6,
                      textWeight: 0.4,
                    })}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-700 hover:border-black dark:hover:border-white hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all duration-300 text-sm tracking-wider uppercase"
                  >
                    {term}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          ) : null}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                OmniSearch: A Multimodal Retrieval and Ranking System
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Cross-Modal E-Commerce Product Discovery
              </p>
            </div>
            <div className="flex gap-6 text-sm">
              <a 
                href="http://localhost:8000/docs" 
                target="_blank" 
                className="text-gray-500 hover:text-black dark:hover:text-white transition-colors tracking-wider uppercase"
              >
                API Docs
              </a>
              <a 
                href="https://github.com/HustleDanie/OmniSearch-A-Multimodal-Retrieval-and-Ranking-System-for-Cross-Modal-E-Commerce-Product-Discovery" 
                target="_blank" 
                className="text-gray-500 hover:text-black dark:hover:text-white transition-colors tracking-wider uppercase"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
