/**
 * OmniSearch API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Product {
  product_id: string;
  title: string;
  description: string;
  color: string;
  category: string;
  image_path: string;
  similarity: number;
  distance: number;
  debug_scores?: Record<string, number>;
}

export interface SearchResponse {
  query: string;
  results: Product[];
  total_results: number;
}

export interface ImageSearchResponse {
  filename: string;
  results: Product[];
  total_results: number;
}

export interface MultimodalSearchResponse {
  text: string | null;
  filename: string | null;
  results: Product[];
  total_results: number;
}

export interface Recommendation {
  title: string;
  product_id: string;
  explanation: string;
  is_wildcard: boolean;
  product_link: string;
}

export interface RecommendResponse {
  user_id: string;
  query: string;
  recommendations: Recommendation[];
  total_recommendations: number;
}

export interface HealthResponse {
  status: string;
  clip_loaded: boolean;
  weaviate_connected: boolean;
  mode?: string;
  message?: string;
}

// Text Search
export async function searchByText(
  query: string,
  options?: {
    top_k?: number;
    category?: string;
    color?: string;
    debug?: boolean;
  }
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search/text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      top_k: options?.top_k || 10,
      category: options?.category || null,
      color: options?.color || null,
      debug: options?.debug || false,
    }),
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

// Image Search
export async function searchByImage(
  file: File,
  options?: {
    top_k?: number;
    category?: string;
    color?: string;
  }
): Promise<ImageSearchResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const params = new URLSearchParams();
  if (options?.top_k) params.append('top_k', options.top_k.toString());
  if (options?.category) params.append('category', options.category);
  if (options?.color) params.append('color', options.color);

  const response = await fetch(`${API_BASE_URL}/search/image?${params}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Image search failed: ${response.statusText}`);
  }

  return response.json();
}

// Multimodal Search (text + image)
export async function searchMultimodal(
  options: {
    text?: string;
    file?: File;
    top_k?: number;
    category?: string;
    color?: string;
    image_weight?: number;
    text_weight?: number;
  }
): Promise<MultimodalSearchResponse> {
  const formData = new FormData();
  
  if (options.text) formData.append('text', options.text);
  if (options.file) formData.append('file', options.file);

  const params = new URLSearchParams();
  if (options.top_k) params.append('top_k', options.top_k.toString());
  if (options.category) params.append('category', options.category);
  if (options.color) params.append('color', options.color);
  if (options.image_weight) params.append('image_weight', options.image_weight.toString());
  if (options.text_weight) params.append('text_weight', options.text_weight.toString());

  const response = await fetch(`${API_BASE_URL}/search/multimodal?${params}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Multimodal search failed: ${response.statusText}`);
  }

  return response.json();
}

// AI Recommendations
export async function getRecommendations(
  userId: string,
  options?: {
    query?: string;
    image?: File;
    top_k?: number;
    image_weight?: number;
    text_weight?: number;
  }
): Promise<RecommendResponse> {
  const formData = new FormData();
  formData.append('user_id', userId);
  
  if (options?.query) formData.append('query', options.query);
  if (options?.image) formData.append('image', options.image);

  const params = new URLSearchParams();
  if (options?.top_k) params.append('top_k', options.top_k.toString());
  if (options?.image_weight) params.append('image_weight', options.image_weight.toString());
  if (options?.text_weight) params.append('text_weight', options.text_weight.toString());

  const response = await fetch(`${API_BASE_URL}/agent/recommend?${params}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Recommendations failed: ${response.statusText}`);
  }

  return response.json();
}

// Health Check
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/search/health`);
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

// Get API Info
export async function getApiInfo(): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/`);
  
  if (!response.ok) {
    throw new Error(`API info failed: ${response.statusText}`);
  }

  return response.json();
}
