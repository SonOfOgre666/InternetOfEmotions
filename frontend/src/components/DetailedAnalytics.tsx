'use client';

import { emotionConfig, type CountryData, type Emotion } from '@/lib/data';
import { getCountryInfo } from '@/lib/countryInfo';
import { logger } from '@/lib/logger';
import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import * as flags from 'country-flag-icons/react/3x2';
import type * as GeoJSONTypes from 'geojson';

const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);
const GeoJSON = dynamic(
  () => import('react-leaflet').then((mod) => mod.GeoJSON),
  { ssr: false }
);

interface DetailedAnalyticsProps {
  country: CountryData;
  onClose: () => void;
}

interface CountryDetail {
  country_emotion: {
    dominant_emotion: string;
    confidence: number;
  };
  emotion_distribution: Record<string, number>;
  total_posts: number;
  recent_posts: Array<{
    title: string;
    text?: string;
    subreddit?: string;
    emotion: string;
    confidence: number;
    urls?: string[];
  }>;
  top_topics: Array<{
    topic: string;
    count: number;
    description?: string;
    urls?: string[];
  }>;
  recent_events?: Array<{
    title: string;
    description: string;
    event_date: string;
    urls: string[];
    post_count: number;
  }>;
  timeline?: Array<{
    day: string;
    confidence: number;
    event_count: number;
  }>;
}

export function DetailedAnalytics({ country, onClose }: DetailedAnalyticsProps) {
  const emotionData = emotionConfig[country.emotion];
  const [geoJsonData, setGeoJsonData] = useState<GeoJSONTypes.FeatureCollection | null>(null);
  const [countryFeature, setCountryFeature] = useState<GeoJSONTypes.Feature | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [countryDetail, setCountryDetail] = useState<CountryDetail | null>(null);
  const [actualDistribution, setActualDistribution] = useState<Record<Emotion, number>>(country.distribution);

  const countryInfo = getCountryInfo(country.name);
  
  const getFlagComponent = (countryName: string) => {
    const info = getCountryInfo(countryName);
    const code = info.iso2;
    const FlagComponent = (flags as Record<string, React.ComponentType<{ className?: string }>>)[code];
    return FlagComponent ? <FlagComponent className="w-12 h-8 rounded shadow-sm" /> : <span className="text-3xl">🏳️</span>;
  };

  // Fetch country details from backend
  useEffect(() => {
    const fetchCountryDetails = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        
        // Fetch country details
        const response = await fetch(`${API_BASE}/api/country/${country.name.toLowerCase()}`);
        if (response.ok) {
          const data = await response.json() as {
            top_emotion?: string;
            confidence?: number;
            emotions?: Record<string, number>;
            total_posts?: number;
            top_topics?: Array<{ topic: string; count: number }>;
            recent_events?: Array<{ title: string; description: string; event_date: string; urls: string[]; post_count: number }>;
          };
          
          // Fetch timeline data
          let timelineData: Array<{ day: string; confidence: number; event_count: number }> = [];
          try {
            const timelineResponse = await fetch(`${API_BASE}/api/timeline/${country.name.toLowerCase()}`);
            if (timelineResponse.ok) {
              const timeline = await timelineResponse.json();
              timelineData = timeline.timeline || [];
            }
          } catch (error) {
            logger.error('Failed to fetch timeline:', error);
          }
          
          // Transform backend data to CountryDetail format
          const detail: CountryDetail = {
            country_emotion: {
              dominant_emotion: data.top_emotion || country.emotion,
              confidence: data.confidence || country.confidence
            },
            emotion_distribution: data.emotions || {},
            total_posts: data.total_posts || country.postCount,
            top_topics: data.top_topics || [],
            recent_posts: [], // Will be populated from recent_events
            recent_events: data.recent_events || [],
            timeline: timelineData
          };
          
          // Transform events to posts format for compatibility
          if (detail.recent_events) {
            detail.recent_posts = detail.recent_events.map(event => ({
              title: event.title,
              text: event.description,
              emotion: country.emotion,
              confidence: country.confidence / 100,
              urls: event.urls
            }));
          }
          
          setCountryDetail(detail);
          
          // Convert backend distribution to frontend format with percentages
          if (data.emotions) {
            const total = Object.values(data.emotions).reduce((sum: number, count) => sum + Number(count), 0);
            const distribution: Record<Emotion, number> = {
              anger: 0,
              fear: 0,
              sadness: 0,
              joy: 0,
              neutral: 0,
              surprise: 0,
              disgust: 0,
            };
            
            Object.entries(data.emotions).forEach(([emotion, count]) => {
              if (emotion in distribution) {
                distribution[emotion as Emotion] = Math.round((Number(count) / total) * 100);
              }
            });
            
            setActualDistribution(distribution);
          }
        }
      } catch (error) {
        logger.error('Failed to fetch country details:', error);
      }
    };
    
    fetchCountryDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [country.name]);

  // Fetch GeoJSON and find country
  useEffect(() => {
    fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
      .then((response) => response.json())
      .then((data) => {
        setGeoJsonData(data);
        
        // Find the feature for the selected country with multiple matching strategies
        const countryNameLower = country.name.toLowerCase();
        const feature = data.features.find(
          (f: GeoJSONTypes.Feature) => {
            const props = f.properties;
            if (!props) return false;
            
            // Try ISO codes first
            if (props.iso_a3 === country.iso || props.iso_a2 === countryInfo.iso2) return true;
            
            // Try exact name match
            if (props.name?.toLowerCase() === countryNameLower) return true;
            
            // Try common name variations
            if (props.formal_en?.toLowerCase() === countryNameLower) return true;
            if (props.name_long?.toLowerCase() === countryNameLower) return true;
            if (props.admin?.toLowerCase() === countryNameLower) return true;
            
            return false;
          }
        );

        if (feature && feature.geometry) {
          setCountryFeature(feature);
          logger.info(`Found GeoJSON for ${country.name}:`, feature.properties?.name);
          
          // Calculate center from geometry
          if (feature.geometry.type === 'Polygon') {
            const coords = feature.geometry.coordinates[0];
            const avgLng = coords.reduce((sum: number, c: number[]) => sum + c[0], 0) / coords.length;
            const avgLat = coords.reduce((sum: number, c: number[]) => sum + c[1], 0) / coords.length;
            setMapCenter([avgLat, avgLng]);
            setMapZoom(4);
          } else if (feature.geometry.type === 'MultiPolygon') {
            const coords = feature.geometry.coordinates[0][0];
            const avgLng = coords.reduce((sum: number, c: number[]) => sum + c[0], 0) / coords.length;
            const avgLat = coords.reduce((sum: number, c: number[]) => sum + c[1], 0) / coords.length;
            setMapCenter([avgLat, avgLng]);
            setMapZoom(3);
          }
        } else {
          logger.warn(`GeoJSON not found for country: ${country.name} (iso: ${country.iso}, iso2: ${countryInfo.iso2})`);
        }
      })
      .catch((error) => logger.error('Error loading GeoJSON:', error));
  }, [country]);

  const styleFeature = () => ({
    fillColor: emotionData.color,
    fillOpacity: 0.7,
    color: '#fbbf24',
    weight: 2,
  });

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-md z-[9999] flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl max-w-[95vw] w-full max-h-[90vh] h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-zinc-900 border-b border-zinc-800 p-4 flex items-center justify-between z-10 flex-shrink-0">
          <div className="flex items-center gap-3">
            {getFlagComponent(country.name)}
            <div>
              <h2 className="text-xl font-bold text-zinc-100">
                {country.name}
              </h2>
              <p className="text-xs text-zinc-400">
                {emotionData.emoji} {emotionData.label} • {country.confidence}% confidence
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <svg
              className="w-5 h-5 text-zinc-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Main Content: Map + Info */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left: Map */}
          <div className="flex-1 bg-zinc-950 relative">
            {/* Capital Overlay */}
            <div className="absolute top-4 left-4 z-[1000] bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-lg px-4 py-2 shadow-xl">
              <div className="flex items-center gap-2">
                <span className="text-lg">⭐</span>
                <div>
                  <p className="text-xs text-zinc-400">Capital City</p>
                  <p className="text-sm font-semibold text-zinc-100">{countryInfo.capital || 'N/A'}</p>
                </div>
              </div>
            </div>
            {countryFeature && (
              <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                style={{ height: '100%', width: '100%', background: '#09090b' }}
                zoomControl={true}
                scrollWheelZoom={true}
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                <GeoJSON
                  data={countryFeature}
                  style={styleFeature}
                />
              </MapContainer>
            )}
            {!countryFeature && (
              <div className="flex items-center justify-center h-full">
                <div className="text-zinc-400 text-sm">Loading map...</div>
              </div>
            )}
          </div>

          {/* Right: Info Panel */}
          <div className="flex-1 bg-zinc-900 border-l border-zinc-800 overflow-y-auto">
            <div className="p-6 space-y-6">
              {/* Dominant Emotion */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-5xl">{emotionData.emoji}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-zinc-100">
                      Dominant Emotion: {emotionData.label.toUpperCase()}
                    </h3>
                    <p className="text-sm text-zinc-400">
                      {country.confidence}% confidence • {country.postCount.toLocaleString()} total posts
                    </p>
                  </div>
                </div>
                <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${country.confidence}%`,
                      backgroundColor: emotionData.color,
                    }}
                  />
                </div>
              </div>

              {/* Emotion Timeline */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-zinc-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  Emotion Confidence Timeline
                </h3>
                <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                  {countryDetail?.timeline && countryDetail.timeline.length > 0 ? (
                    <>
                      <div className="flex items-end justify-between h-32 gap-1">
                        {countryDetail.timeline.map((item, index) => (
                          <div
                            key={index}
                            className="flex-1 bg-gradient-to-t from-zinc-700 to-zinc-600 rounded-t hover:from-zinc-600 hover:to-zinc-500 transition-all cursor-pointer"
                            style={{ height: `${item.confidence}%` }}
                            title={`${item.day}: ${item.confidence}% confidence, ${item.event_count} events`}
                          />
                        ))}
                      </div>
                      <div className="flex items-center justify-between text-xs text-zinc-500 mt-2">
                        <span>{countryDetail.timeline.length}d ago</span>
                        <span>Today</span>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 text-zinc-500 text-sm">
                      Not enough data for timeline (need 7+ days)
                    </div>
                  )}
                </div>
              </div>

              {/* Distribution */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4">
                  Emotion Distribution
                </h3>
                <div className="space-y-3">
              {Object.entries(actualDistribution).map(([emotion, percentage]) => {
                const config = emotionConfig[emotion as Emotion];
                if (!config) return null;
                return (
                  <div key={emotion}>
                    <div className="flex items-center justify-between text-sm mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{config.emoji}</span>
                        <span className="text-zinc-300">{config.label}</span>
                      </div>
                      <span className="text-zinc-400 font-mono">{percentage}%</span>
                    </div>
                    <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${percentage}%`,
                          backgroundColor: config.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
                </div>
              </div>

              {/* Top Topics */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-zinc-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                    />
                  </svg>
                  Top Discussion Topics
                </h3>
                <div className="space-y-3">
              {countryDetail?.top_topics && countryDetail.top_topics.length > 0 ? (
                countryDetail.top_topics.map((topic, index) => (
                  <div
                    key={index}
                    className="p-3 bg-zinc-900 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-zinc-500 font-mono text-sm mt-0.5">#{index + 1}</span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-zinc-200 text-sm font-medium mb-1 leading-snug">
                          {topic.topic}
                        </h4>
                        {topic.description && (
                          <p className="text-zinc-400 text-xs mb-2 leading-relaxed">
                            {topic.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-zinc-500 font-mono">
                            {topic.count} {topic.count === 1 ? 'post' : 'posts'}
                          </span>
                          {topic.urls && topic.urls.length > 0 && topic.urls[0] && (
                            <a
                              href={topic.urls[0]}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
                            >
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                              Source
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-zinc-500 text-sm text-center py-4">No topics available</p>
              )}
                </div>
              </div>

              {/* Recent Events */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4">
                  Recent Events from {country.name}
                </h3>
                <div className="space-y-3">
              {countryDetail?.recent_events && countryDetail.recent_events.length > 0 ? (
                countryDetail.recent_events.map((event, index) => (
                  <div
                    key={index}
                    className="p-4 bg-zinc-900 rounded-lg border border-zinc-800"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-sm font-semibold text-zinc-100">{event.title}</h4>
                      <span className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400">
                        📊 {event.post_count} posts
                      </span>
                    </div>
                    {event.description && <p className="text-xs text-zinc-400 mb-2">{event.description}</p>}
                    <div className="text-xs text-zinc-500">
                      {event.event_date && (
                        <div className="mb-2">
                          📅 {new Date(event.event_date).toLocaleDateString()}
                        </div>
                      )}
                      {event.urls && event.urls.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {event.urls.map((url, idx) => (
                            <a
                              key={idx}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-amber-500 hover:text-amber-400 block truncate"
                            >
                              🔗 {url}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-zinc-500 text-sm text-center py-4">No recent events available</p>
              )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-750 border border-zinc-700 rounded-lg text-xs font-medium text-zinc-100 transition-colors flex items-center justify-center gap-2">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Export
                </button>
                <button className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-750 border border-zinc-700 rounded-lg text-xs font-medium text-zinc-100 transition-colors flex items-center justify-center gap-2">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  Compare
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
