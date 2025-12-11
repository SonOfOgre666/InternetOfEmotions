'use client';

import { useState, useEffect, useCallback } from 'react';
import type { CountryData, Emotion } from './data';
import { emotionConfig } from './data';
import {
  fetchEmotions,
  fetchStats,
  fetchHealth,
  createPostStream,
  type BackendPost,
  type BackendStats,
} from './api';

interface UseBackendReturn {
  countries: CountryData[];
  isConnected: boolean;
  isBackendAvailable: boolean;
  demoMode: boolean;
  stats: BackendStats | null;
  recentPosts: BackendPost[];
  error: string | null;
}

/**
 * Custom hook to manage backend connection and data
 */
export function useBackend(): UseBackendReturn {
  const [countries, setCountries] = useState<CountryData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [stats, setStats] = useState<BackendStats | null>(null);
  const [recentPosts, setRecentPosts] = useState<BackendPost[]>([]);
  const [error, setError] = useState<string | null>(null);

  /**
   * Convert backend posts to CountryData
   */
  const convertPostsToCountries = useCallback((posts: BackendPost[]): CountryData[] => {
    // Group posts by country
    const countryMap = new Map<string, BackendPost[]>();
    
    posts.forEach((post) => {
      const countryName = post.country;
      if (!countryMap.has(countryName)) {
        countryMap.set(countryName, []);
      }
      countryMap.get(countryName)!.push(post);
    });

    // Convert to CountryData
    const countriesData: CountryData[] = [];
    
    countryMap.forEach((countryPosts, countryName) => {
      // Calculate dominant emotion
      const emotionCounts: Record<Emotion, number> = {
        anger: 0,
        fear: 0,
        sadness: 0,
        joy: 0,
        neutral: 0,
        surprise: 0,
        disgust: 0,
      };

      countryPosts.forEach((post) => {
        emotionCounts[post.emotion]++;
      });

      // Find dominant emotion
      let dominantEmotion: Emotion = 'neutral';
      let maxCount = 0;
      
      Object.entries(emotionCounts).forEach(([emotion, count]) => {
        if (count > maxCount) {
          maxCount = count;
          dominantEmotion = emotion as Emotion;
        }
      });

      // Calculate confidence (average of all posts)
      const avgConfidence = Math.round(
        countryPosts.reduce((sum, p) => sum + p.confidence, 0) / countryPosts.length
      );

      // Get distribution percentages
      const total = countryPosts.length;
      const distribution: Record<Emotion, number> = {} as Record<Emotion, number>;
      
      Object.entries(emotionCounts).forEach(([emotion, count]) => {
        distribution[emotion as Emotion] = Math.round((count / total) * 100);
      });

      // Extract top topics (from titles)
      const topTopics = countryPosts
        .slice(0, 5)
        .map((p) => ({ topic: p.title.slice(0, 50), count: 1 }));

      // Get recent posts
      const recentPostsText = countryPosts
        .slice(0, 3)
        .map((p) => p.title);

      // Map country name to ISO code (simplified mapping)
      const iso = getCountryISO(countryName);
      const emoji = getCountryEmoji(countryName);

      countriesData.push({
        iso,
        name: countryName,
        emoji,
        capital: '', // Not provided by backend
        emotion: dominantEmotion,
        confidence: avgConfidence,
        postCount: countryPosts.length,
        trend: 'steady', // Could calculate from historical data
        distribution,
        topTopics,
        recentPosts: recentPostsText,
      });
    });

    return countriesData;
  }, []);

  /**
   * Load initial data from backend
   */
  const loadData = useCallback(async () => {
    try {
      // Fetch health status
      const health = await fetchHealth();
      setDemoMode(health.demo_mode);
      setIsBackendAvailable(true);

      // Fetch emotions
      const emotionsData = await fetchEmotions();
      const convertedCountries = convertPostsToCountries(emotionsData.emotions);
      setCountries(convertedCountries);

      // Fetch stats
      const statsData = await fetchStats();
      setStats(statsData);

      setError(null);
    } catch (err) {
      console.error('Failed to load backend data:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      setIsBackendAvailable(false);
    }
  }, [convertPostsToCountries]);

  /**
   * Connect to SSE stream for real-time updates
   */
  useEffect(() => {
    if (!isBackendAvailable) return;

    const eventSource = createPostStream(
      (post) => {
        // Add to recent posts
        setRecentPosts((prev) => [post, ...prev.slice(0, 19)]);

        // Update countries data
        setCountries((prev) => {
          const updated = [...prev];
          const countryIndex = updated.findIndex(
            (c) => c.name.toLowerCase() === post.country.toLowerCase()
          );

          if (countryIndex >= 0) {
            // Update existing country
            const country = updated[countryIndex];
            updated[countryIndex] = {
              ...country,
              postCount: country.postCount + 1,
            };
          }

          return updated;
        });

        // Occasionally refresh stats
        if (Math.random() < 0.1) {
          fetchStats().then(setStats).catch(console.error);
        }
      },
      () => {
        setIsConnected(true);
        setIsBackendAvailable(true);
      },
      () => {
        setIsConnected(false);
        // Retry connection after 10 seconds
        setTimeout(() => {
          setIsBackendAvailable(true);
        }, 10000);
      }
    );

    return () => {
      eventSource.close();
    };
  }, [isBackendAvailable]);

  /**
   * Initial data load and periodic refresh
   */
  useEffect(() => {
    loadData();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      if (isBackendAvailable) {
        loadData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isBackendAvailable, loadData]);

  return {
    countries,
    isConnected,
    isBackendAvailable,
    demoMode,
    stats,
    recentPosts,
    error,
  };
}

/**
 * Helper function to get ISO code from country name
 */
function getCountryISO(countryName: string): string {
  const mapping: Record<string, string> = {
    'united states': 'USA',
    'united kingdom': 'GBR',
    'germany': 'DEU',
    'france': 'FRA',
    'india': 'IND',
    'japan': 'JPN',
    'brazil': 'BRA',
    'canada': 'CAN',
    'australia': 'AUS',
    'china': 'CHN',
    // Add more as needed
  };
  
  return mapping[countryName.toLowerCase()] || countryName.toUpperCase().slice(0, 3);
}

/**
 * Helper function to get emoji from country name
 */
function getCountryEmoji(countryName: string): string {
  const mapping: Record<string, string> = {
    'united states': '🇺🇸',
    'united kingdom': '🇬🇧',
    'germany': '🇩🇪',
    'france': '🇫🇷',
    'india': '🇮🇳',
    'japan': '🇯🇵',
    'brazil': '🇧🇷',
    'canada': '🇨🇦',
    'australia': '🇦🇺',
    'china': '🇨🇳',
    // Add more as needed
  };
  
  return mapping[countryName.toLowerCase()] || '🌍';
}
