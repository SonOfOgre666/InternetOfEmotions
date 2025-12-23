'use client';

import { emotionConfig, type CountryData } from '@/lib/data';
import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import * as flags from 'country-flag-icons/react/3x2';
import type * as GeoJSONTypes from 'geojson';
import { getIso2 } from '@/lib/utils';

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

export function DetailedAnalytics({ country, onClose }: DetailedAnalyticsProps) {
  const emotionData = emotionConfig[country.emotion];
  const [geoJsonData, setGeoJsonData] = useState<GeoJSONTypes.FeatureCollection | null>(null);
  const [countryFeature, setCountryFeature] = useState<GeoJSONTypes.Feature | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);

  const getFlagComponent = (iso: string) => {
    const code = getIso2(iso);
    const FlagComponent = (flags as Record<string, React.ComponentType<{ className?: string }>>)[code];
    return FlagComponent ? <FlagComponent className="w-12 h-8 rounded shadow-sm" /> : <span className="text-3xl">🏳️</span>;
  };

  // Fetch GeoJSON and find country
  useEffect(() => {
    fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
      .then((response) => response.json())
      .then((data) => {
        setGeoJsonData(data);
        
        // Find the feature for the selected country
        const feature = data.features.find(
          (f: GeoJSONTypes.Feature) =>
            f.properties?.iso_a3 === country.iso ||
            f.properties?.iso_a2 === country.iso ||
            f.properties?.name === country.name
        );

        if (feature && feature.geometry) {
          setCountryFeature(feature);
          
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
        }
      })
      .catch((error) => console.error('Error loading GeoJSON:', error));
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
            {getFlagComponent(country.iso)}
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
                  <p className="text-sm font-semibold text-zinc-100">{country.capital}</p>
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
                  Emotion Timeline (Last 7 Days)
                </h3>
                <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                  <div className="flex items-end justify-between h-32 gap-1">
                    {[65, 45, 52, 78, 82, 88, 92].map((height, index) => (
                      <div
                        key={index}
                        className="flex-1 bg-gradient-to-t from-zinc-700 to-zinc-600 rounded-t hover:from-zinc-600 hover:to-zinc-500 transition-all cursor-pointer"
                        style={{ height: `${height}%` }}
                        title={`Day ${index + 1}: ${height}%`}
                      />
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-xs text-zinc-500 mt-2">
                    <span>7d ago</span>
                    <span>Today</span>
                  </div>
                </div>
              </div>

              {/* Distribution */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4">
                  Emotion Distribution
                </h3>
                <div className="space-y-3">
              {Object.entries(country.distribution).map(([emotion, percentage]) => {
                const config = emotionConfig[emotion as keyof typeof country.distribution];
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
              {country.topTopics.map((topic, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-zinc-900 rounded-lg border border-zinc-800"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-500 font-mono text-sm">#{index + 1}</span>
                    <span className="text-zinc-200 text-sm">{topic.topic}</span>
                  </div>
                  <span className="text-zinc-400 text-sm font-mono">
                    {topic.count} posts
                  </span>
                  </div>
                ))}
                </div>
              </div>

              {/* Recent Posts */}
              <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-4">
                  Recent Posts from {country.name}
                </h3>
                <div className="space-y-3">
              {country.recentPosts.map((post, index) => (
                <div
                  key={index}
                  className="p-4 bg-zinc-900 rounded-lg border border-zinc-800 text-sm text-zinc-300"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-zinc-500 mt-1">•</span>
                    <p>{post}</p>
                  </div>
                  </div>
                ))}
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
