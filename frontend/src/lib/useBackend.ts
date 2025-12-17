'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { CountryData, Emotion } from './data';
import { emotionConfig } from './data';
import { getCountryInfo } from './countryInfo';
import {
  fetchEmotions,
  fetchStats,
  fetchHealth,
  createPostStream,
  type BackendPost,
  type BackendStats,
} from './api';
import { logger } from './logger';

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
   * Convert backend country aggregation data to CountryData format
   * Backend sends aggregated country emotions with coords, not individual posts
   */
  const convertBackendToCountries = useCallback((backendData: BackendPost[]): CountryData[] => {
    // Backend sends country aggregations, not individual posts
    // Each item has: id, country, emotion, confidence, coords, post_count
    return backendData.map((item) => {
      const countryName = item.country;
      const countryInfo = getCountryInfo(countryName);

      // Initialize empty distribution
      const distribution: Record<Emotion, number> = {
        anger: 0,
        fear: 0,
        sadness: 0,
        joy: 0,
        neutral: 0,
        surprise: 0,
        disgust: 0,
      };
      
      // Set dominant emotion confidence, distribute remaining across others
      const confidence = Math.round(item.confidence * 100);
      distribution[item.emotion] = confidence;
      
      // Distribute remaining percentage equally among other emotions
      const remaining = 100 - confidence;
      const otherEmotions = (Object.keys(emotionConfig) as Emotion[]).filter(e => e !== item.emotion);
      const perEmotion = Math.floor(remaining / otherEmotions.length);
      otherEmotions.forEach(emotion => {
        distribution[emotion] = perEmotion;
      });

      return {
        iso: countryInfo.iso3,
        name: countryName,
        emoji: '🌍', // Placeholder - actual flags rendered by country-flag-icons library
        capital: countryInfo.capital,
        emotion: item.emotion,
        confidence,
        postCount: item.post_count || 0,
        trend: 'steady' as const,
        distribution,
        topTopics: [], // Not provided in aggregation endpoint
        recentPosts: [], // Not provided in aggregation endpoint
      };
    });
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

      // Fetch emotions (country aggregations)
      const emotionsData = await fetchEmotions();
      const convertedCountries = convertBackendToCountries(emotionsData.emotions);
      setCountries(convertedCountries);

      // Fetch stats
      const statsData = await fetchStats();
      setStats(statsData);

      setError(null);
    } catch (err) {
      logger.error('Failed to load backend data:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      setIsBackendAvailable(false);
      // Set empty arrays instead of using mock data
      setCountries([]);
    }
  }, [convertBackendToCountries]);

  /**
   * Connect to SSE stream for real-time updates
   */
  const retryCountRef = useRef(0);
  const maxRetries = 10;
  
  useEffect(() => {
    if (!isBackendAvailable) return;

    const eventSource = createPostStream(
      () => {
        // Stats stream triggered an update, reload data
        retryCountRef.current = 0; // Reset retry count on successful message
        if (isBackendAvailable) {
          loadData();
        }
      },
      () => {
        setIsConnected(true);
        setIsBackendAvailable(true);
        retryCountRef.current = 0; // Reset on successful connection
      },
      () => {
        setIsConnected(false);
        
        // Exponential backoff: 2^retryCount * 1000ms, max 60 seconds
        if (retryCountRef.current < maxRetries) {
          const delay = Math.min(Math.pow(2, retryCountRef.current) * 1000, 60000);
          retryCountRef.current += 1;
          
          setTimeout(() => {
            if (isBackendAvailable) {
              // Reconnect SSE stream after backoff
              loadData();
              // Note: The useEffect will create a new EventSource when deps change
            }
          }, delay);
        } else {
          logger.error('Max SSE reconnection attempts reached');
          setIsBackendAvailable(false);
        }
      }
    );

    return () => {
      eventSource.close();
    };
  }, [isBackendAvailable, loadData]);

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
