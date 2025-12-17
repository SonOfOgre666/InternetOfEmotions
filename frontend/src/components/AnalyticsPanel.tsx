'use client';

import { emotionConfig, type CountryData } from '@/lib/data';
import { getCountryInfo } from '@/lib/countryInfo';
import { type BackendStats } from '@/lib/api';
import * as flags from 'country-flag-icons/react/3x2';

interface AnalyticsPanelProps {
  stats: BackendStats | null;
  countries: CountryData[];
}

export function AnalyticsPanel({ stats, countries }: AnalyticsPanelProps) {
  const topCountries = [...countries]
    .sort((a, b) => b.postCount - a.postCount)
    .slice(0, 10);

  const getFlagComponent = (countryName: string) => {
    const info = getCountryInfo(countryName);
    const code = info.iso2;
    const FlagComponent = (flags as Record<string, React.ComponentType<{ className?: string }>>)[code];
    return FlagComponent ? <FlagComponent className="w-5 h-3 rounded" /> : <span>🏳️</span>;
  };

  const getTrendIcon = (direction: 'up' | 'down' | 'steady') => {
    if (direction === 'up') return '▲';
    if (direction === 'down') return '▼';
    return '▬';
  };

  const getTrendColor = (direction: 'up' | 'down' | 'steady') => {
    if (direction === 'up') return 'text-red-500';
    if (direction === 'down') return 'text-green-500';
    return 'text-zinc-400';
  };

  if (!stats) {
    return (
      <div className="border-t border-zinc-800 bg-zinc-900">
        <div className="p-4">
          <h2 className="text-sm font-semibold text-zinc-100 mb-4 flex items-center gap-2">
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
            Global Analytics Dashboard
          </h2>
          <div className="text-center py-8 text-zinc-500 text-sm">
            No analytics data available
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
      <div className="p-3">
        <h2 className="text-xs font-semibold text-zinc-100 mb-3 flex items-center gap-2">
          <svg
            className="w-3.5 h-3.5 text-zinc-400"
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
          Global Analytics
        </h2>

        <div className="grid grid-cols-3 gap-3">
          {/* Emotion Distribution */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-3">
            <h3 className="text-[10px] font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
              Emotion Distribution
            </h3>
            <div className="space-y-1.5">
              {Object.entries(stats.by_emotion).map(([emotion, count]) => {
                const config = emotionConfig[emotion as keyof typeof emotionConfig];
                const percentage = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
                return (
                  <div
                    key={emotion}
                    className="flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">{config.emoji}</span>
                      <span className="text-zinc-300">{config.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500">{count}</span>
                      <span className="text-zinc-400">({percentage}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Countries */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-3">
            <h3 className="text-[10px] font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
              Top Countries
            </h3>
            <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-zinc-850">
              {topCountries.length === 0 ? (
                <div className="text-center py-4 text-zinc-500 text-xs">
                  No country data available
                </div>
              ) : (
                topCountries.map((country, index) => (
                  <div
                    key={country.iso}
                    className="flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500 font-mono w-4">{index + 1}.</span>
                      <span className="text-base">{getFlagComponent(country.name)}</span>
                      <span className="text-zinc-300">{country.name}</span>
                    </div>
                    <span className="text-zinc-500 font-mono">
                      {country.postCount.toLocaleString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* System Metrics */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-3">
            <h3 className="text-[10px] font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
              System Metrics
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Total Posts</span>
                <span className="text-zinc-100 font-semibold">
                  {stats.total.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Active Emotions</span>
                <span className="text-zinc-100 font-semibold">
                  {Object.keys(stats.by_emotion).length}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Countries with Data</span>
                <span className="text-zinc-100 font-semibold">
                  {Object.keys(stats.by_country).length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
