import type { Emotion } from './data';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export interface BackendPost {
  id: string;
  country: string;
  emotion: Emotion;
  confidence: number;
  title: string;
  text: string;
  timestamp: number;
  subreddit: string;
  url: string;
  latitude?: number;
  longitude?: number;
}

export interface BackendStats {
  total: number;
  by_emotion: Record<string, number>;
  by_country: Record<string, number>;
  countries_ready: number;
  max_age_days: number;
}

export interface BackendEmotionsResponse {
  emotions: BackendPost[];
  count: number;
  countries_ready: number;
  max_age_days: number;
}

export interface BackendHealthResponse {
  status: string;
  demo_mode: boolean;
  db_posts: number;
  last_fetch?: string;
}

/**
 * Fetch emotions from backend
 */
export async function fetchEmotions(): Promise<BackendEmotionsResponse> {
  const response = await fetch(`${API_BASE}/api/emotions`, {
    cache: 'no-store',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch emotions: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Fetch statistics from backend
 */
export async function fetchStats(): Promise<BackendStats> {
  const response = await fetch(`${API_BASE}/api/stats`, {
    cache: 'no-store',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Fetch health status from backend
 */
export async function fetchHealth(): Promise<BackendHealthResponse> {
  const response = await fetch(`${API_BASE}/api/health`, {
    cache: 'no-store',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch health: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create SSE connection for real-time posts
 */
export function createPostStream(
  onMessage: (post: BackendPost) => void,
  onOpen?: () => void,
  onError?: (error: Event) => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE}/api/posts/stream`);
  
  eventSource.onopen = () => {
    console.log('✓ Connected to emotion stream');
    onOpen?.();
  };
  
  eventSource.onmessage = (event) => {
    try {
      const post = JSON.parse(event.data) as BackendPost;
      onMessage(post);
    } catch (error) {
      console.error('Failed to parse SSE message:', error);
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('Stream error:', error);
    onError?.(error);
  };
  
  return eventSource;
}
