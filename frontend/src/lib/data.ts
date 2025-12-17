export type Emotion = 'anger' | 'fear' | 'sadness' | 'joy' | 'neutral' | 'surprise' | 'disgust';

export interface EventData {
  title: string;
  description: string;
  urls: string[];
  event_date: string;
}

export interface CountryData {
  iso: string;
  name: string;
  emoji: string;
  capital: string;
  emotion: Emotion;
  confidence: number;
  postCount: number;
  trend: 'up' | 'down' | 'steady';
  distribution: Record<Emotion, number>;
  topTopics: { topic: string; count: number }[];
  recentPosts: string[];
  recentEvents?: EventData[];
}

export const emotionConfig = {
  anger: { label: 'Anger', emoji: '😡', color: '#ef4444' },
  fear: { label: 'Fear', emoji: '😨', color: '#f97316' },
  sadness: { label: 'Sadness', emoji: '😭', color: '#6366f1' },
  joy: { label: 'Joy', emoji: '🥳', color: '#22c55e' },
  neutral: { label: 'Neutral', emoji: '😶', color: '#94a3b8' },
  surprise: { label: 'Surprise', emoji: '😱', color: '#a855f7' },
  disgust: { label: 'Disgust', emoji: '🤮', color: '#84cc16' },
};

// No mock data - frontend uses real backend API only
// All data comes from:
// - /api/emotions (country aggregation)
// - /api/stats (statistics)
// - /api/posts/stream (SSE updates)
