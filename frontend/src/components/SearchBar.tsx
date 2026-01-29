'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Image, X, SlidersHorizontal, Upload, Zap } from 'lucide-react';

export interface SearchOptions {
  top_k: number;
  category: string;
  color: string;
  searchType: 'text' | 'image' | 'multimodal';
  imageWeight: number;
  textWeight: number;
}

interface SearchBarProps {
  onSearch: (query: string, file: File | null, options: SearchOptions) => void;
  isLoading: boolean;
}

const CATEGORIES = ['All', 'dresses', 'pants', 'tops', 'shoes', 'accessories'];
const COLORS = ['All', 'red', 'blue', 'green', 'black', 'white', 'multicolor'];

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [options, setOptions] = useState<SearchOptions>({
    top_k: 10,
    category: 'All',
    color: 'All',
    searchType: 'text',
    imageWeight: 0.6,
    textWeight: 0.4,
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      if (!query) {
        setOptions(prev => ({ ...prev, searchType: 'image' }));
      } else {
        setOptions(prev => ({ ...prev, searchType: 'multimodal' }));
      }
    }
  };

  const clearFile = () => {
    setFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setOptions(prev => ({ ...prev, searchType: query ? 'text' : 'text' }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query && !file) return;
    
    let searchType = options.searchType;
    if (file && query) searchType = 'multimodal';
    else if (file) searchType = 'image';
    else searchType = 'text';

    onSearch(query, file, { ...options, searchType });
  };

  const searchTypeLabel = file && query ? 'MULTIMODAL' : file ? 'IMAGE' : 'TEXT';
  const searchTypeColor = file && query ? 'purple' : file ? 'green' : 'blue';

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto space-y-4">
      {/* Main Search Container */}
      <div className="relative">
        {/* Decorative Corners */}
        <div className="absolute -top-2 -left-2 w-6 h-6 border-t-2 border-l-2 border-black dark:border-white" />
        <div className="absolute -top-2 -right-2 w-6 h-6 border-t-2 border-r-2 border-black dark:border-white" />
        <div className="absolute -bottom-2 -left-2 w-6 h-6 border-b-2 border-l-2 border-black dark:border-white" />
        <div className="absolute -bottom-2 -right-2 w-6 h-6 border-b-2 border-r-2 border-black dark:border-white" />

        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-4 md:p-6">
          {/* Search Type Badge */}
          <div className="flex justify-between items-center mb-4">
            <span className={`text-xs tracking-widest font-mono px-3 py-1 border ${
              searchTypeColor === 'purple' ? 'border-purple-500 text-purple-500' :
              searchTypeColor === 'green' ? 'border-green-500 text-green-500' :
              'border-blue-500 text-blue-500'
            }`}>
              {searchTypeLabel} SEARCH
            </span>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-3 py-1 text-xs tracking-widest transition-all ${
                showFilters 
                  ? 'bg-black text-white dark:bg-white dark:text-black' 
                  : 'border border-gray-300 dark:border-gray-700 hover:border-black dark:hover:border-white'
              }`}
            >
              <SlidersHorizontal className="w-3 h-3" />
              FILTERS
            </button>
          </div>

          {/* Input Row */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter search query..."
                className="w-full px-4 py-4 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 focus:border-black dark:focus:border-white outline-none transition-colors font-mono text-sm placeholder:text-gray-400"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-400 hover:text-black dark:hover:text-white transition-colors"
                  title="Upload image"
                >
                  <Upload className="w-5 h-5" />
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
            
            <motion.button
              type="submit"
              disabled={isLoading || (!query && !file)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 md:px-8 py-4 bg-black dark:bg-white text-white dark:text-black font-mono text-sm tracking-wider disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Zap className="w-4 h-4" />
                  </motion.div>
                  <span className="hidden md:inline">SEARCHING...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span className="hidden md:inline">SEARCH</span>
                </>
              )}
            </motion.button>
          </div>

          {/* Image Preview */}
          <AnimatePresence>
            {previewUrl && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 overflow-hidden"
              >
                <div className="flex items-center gap-4 p-3 border border-gray-200 dark:border-gray-800 bg-white dark:bg-black">
                  <div className="relative">
                    <img src={previewUrl} alt="Search image" className="h-16 w-16 object-cover" />
                    <div className="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-black dark:border-white" />
                    <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-black dark:border-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-mono truncate">{file?.name}</p>
                    <p className="text-xs text-gray-500 font-mono mt-1">
                      {query ? 'Combined with text query' : 'Image-only search'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={clearFile}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Filters Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 overflow-hidden"
              >
                <div className="pt-4 border-t border-gray-200 dark:border-gray-800 space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Results count */}
                    <div>
                      <label className="block text-xs font-mono tracking-wider text-gray-500 mb-2">
                        RESULTS
                      </label>
                      <select
                        value={options.top_k}
                        onChange={(e) => setOptions(prev => ({ ...prev, top_k: Number(e.target.value) }))}
                        className="w-full px-3 py-2 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 focus:border-black dark:focus:border-white outline-none font-mono text-sm"
                      >
                        {[5, 10, 20, 50].map(n => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                    </div>

                    {/* Category */}
                    <div>
                      <label className="block text-xs font-mono tracking-wider text-gray-500 mb-2">
                        CATEGORY
                      </label>
                      <select
                        value={options.category}
                        onChange={(e) => setOptions(prev => ({ ...prev, category: e.target.value }))}
                        className="w-full px-3 py-2 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 focus:border-black dark:focus:border-white outline-none font-mono text-sm"
                      >
                        {CATEGORIES.map(cat => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                    </div>

                    {/* Color */}
                    <div>
                      <label className="block text-xs font-mono tracking-wider text-gray-500 mb-2">
                        COLOR
                      </label>
                      <select
                        value={options.color}
                        onChange={(e) => setOptions(prev => ({ ...prev, color: e.target.value }))}
                        className="w-full px-3 py-2 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 focus:border-black dark:focus:border-white outline-none font-mono text-sm"
                      >
                        {COLORS.map(color => (
                          <option key={color} value={color}>{color}</option>
                        ))}
                      </select>
                    </div>

                    {/* Search Mode Indicator */}
                    <div>
                      <label className="block text-xs font-mono tracking-wider text-gray-500 mb-2">
                        MODE
                      </label>
                      <div className="px-3 py-2 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 text-center">
                        <span className={`inline-block text-xs font-mono tracking-wider ${
                          file && query ? 'text-purple-500' : file ? 'text-green-500' : 'text-blue-500'
                        }`}>
                          {file && query ? '⚡ HYBRID' : file ? '🖼 VISUAL' : '📝 TEXT'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Multimodal Weights */}
                  {file && query && (
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
                      <label className="block text-xs font-mono tracking-wider text-gray-500 mb-3">
                        WEIGHT DISTRIBUTION
                      </label>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-mono w-24">
                          IMG: {(options.imageWeight * 100).toFixed(0)}%
                        </span>
                        <div className="flex-1 relative h-2 bg-gray-200 dark:bg-gray-800">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={options.imageWeight * 100}
                            onChange={(e) => {
                              const imgWeight = Number(e.target.value) / 100;
                              setOptions(prev => ({
                                ...prev,
                                imageWeight: imgWeight,
                                textWeight: 1 - imgWeight
                              }));
                            }}
                            className="absolute inset-0 w-full opacity-0 cursor-pointer"
                          />
                          <div 
                            className="h-full bg-black dark:bg-white transition-all"
                            style={{ width: `${options.imageWeight * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-mono w-24 text-right">
                          TXT: {(options.textWeight * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </form>
  );
}
