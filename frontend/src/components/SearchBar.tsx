'use client';

import { useState, useRef } from 'react';
import { Product } from '@/lib/api';

interface SearchBarProps {
  onSearch: (query: string, file: File | null, options: SearchOptions) => void;
  isLoading: boolean;
}

export interface SearchOptions {
  top_k: number;
  category: string;
  color: string;
  searchType: 'text' | 'image' | 'multimodal';
  imageWeight: number;
  textWeight: number;
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
    
    // Determine search type
    let searchType = options.searchType;
    if (file && query) searchType = 'multimodal';
    else if (file) searchType = 'image';
    else searchType = 'text';

    onSearch(query, file, { ...options, searchType });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto space-y-4">
      {/* Main Search Input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for products... (e.g., 'red summer dress')"
            className="w-full px-4 py-3 pr-12 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-blue-500 transition-colors"
            title="Upload image"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading || (!query && !file)}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Searching...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </>
          )}
        </button>

        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-3 rounded-xl font-medium transition-colors ${showFilters ? 'bg-gray-200 dark:bg-gray-700' : 'bg-gray-100 dark:bg-gray-800'} hover:bg-gray-200 dark:hover:bg-gray-700`}
          title="Filters"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
        </button>
      </div>

      {/* Image Preview */}
      {previewUrl && (
        <div className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
          <img src={previewUrl} alt="Search image" className="h-16 w-16 object-cover rounded-lg" />
          <div className="flex-1">
            <p className="text-sm font-medium dark:text-white">{file?.name}</p>
            <p className="text-xs text-gray-500">
              {query ? 'Multimodal search (text + image)' : 'Image search'}
            </p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Results count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Results
              </label>
              <select
                value={options.top_k}
                onChange={(e) => setOptions(prev => ({ ...prev, top_k: Number(e.target.value) }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                {[5, 10, 20, 50].map(n => (
                  <option key={n} value={n}>{n} results</option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                value={options.category}
                onChange={(e) => setOptions(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            {/* Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Color
              </label>
              <select
                value={options.color}
                onChange={(e) => setOptions(prev => ({ ...prev, color: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                {COLORS.map(color => (
                  <option key={color} value={color}>{color}</option>
                ))}
              </select>
            </div>

            {/* Search Type Badge */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Search Type
              </label>
              <div className="px-3 py-2 bg-white dark:bg-gray-700 border rounded-lg text-center">
                <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                  file && query ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' :
                  file ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                  'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                }`}>
                  {file && query ? '🔀 Multimodal' : file ? '🖼️ Image' : '📝 Text'}
                </span>
              </div>
            </div>
          </div>

          {/* Multimodal Weights (only show when both text and image) */}
          {file && query && (
            <div className="pt-4 border-t dark:border-gray-700">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Multimodal Weights
              </label>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500 w-20">Image: {(options.imageWeight * 100).toFixed(0)}%</span>
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
                  className="flex-1"
                />
                <span className="text-sm text-gray-500 w-20">Text: {(options.textWeight * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}
        </div>
      )}
    </form>
  );
}
