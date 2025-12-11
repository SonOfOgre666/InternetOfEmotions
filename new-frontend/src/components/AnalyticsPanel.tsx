'use client';

import { globalStats, emotionConfig, countriesData } from '@/lib/data';
import * as flags from 'country-flag-icons/react/3x2';

export function AnalyticsPanel() {
  const topCountries = [...countriesData]
    .sort((a, b) => b.postCount - a.postCount)
    .slice(0, 10);

  const getFlagComponent = (iso: string) => {
    const isoMap: Record<string, string> = {
      'USA': 'US', 'GBR': 'GB', 'DEU': 'DE', 'FRA': 'FR', 'IND': 'IN',
      'JPN': 'JP', 'BRA': 'BR', 'CAN': 'CA', 'AUS': 'AU', 'CHN': 'CN',
    };
    const code = isoMap[iso] || iso;
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

        <div className="grid grid-cols-3 gap-4">
          {/* Emotion Trends */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
            <h3 className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wide">
              Emotion Trends (24h)
            </h3>
            <div className="space-y-2">
              {Object.entries(globalStats.emotionTrends).map(([emotion, data]) => {
                const config = emotionConfig[emotion as keyof typeof emotionConfig];
                return (
                  <div
                    key={emotion}
                    className="flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">{config.emoji}</span>
                      <span className="text-zinc-300">{config.label}</span>
                    </div>
                    <div className={`flex items-center gap-1 font-medium ${getTrendColor(data.direction)}`}>
                      <span>{getTrendIcon(data.direction)}</span>
                      <span>{data.change}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Countries */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
            <h3 className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wide">
              Top Countries by Activity
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-zinc-850">
              {topCountries.map((country, index) => (
                <div
                  key={country.iso}
                  className="flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-500 font-mono w-4">{index + 1}.</span>
                    <span className="text-base">{getFlagComponent(country.iso)}</span>
                    <span className="text-zinc-300">{country.name}</span>
                  </div>
                  <span className="text-zinc-500 font-mono">
                    {country.postCount.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Real-time Metrics */}
          <div className="bg-zinc-850 rounded-lg border border-zinc-800 p-4">
            <h3 className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wide">
              Real-time System Metrics
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-zinc-400">Posts/Minute</span>
                  <span className="text-zinc-100 font-semibold">
                    {globalStats.postsPerMinute}
                  </span>
                </div>
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: '70%' }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-zinc-400">Active Countries</span>
                  <span className="text-zinc-100 font-semibold">
                    {globalStats.activeCountries}
                  </span>
                </div>
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: '74%' }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Cycle Progress</span>
                <span className="text-zinc-100 font-mono font-semibold">
                  {globalStats.cycleProgress}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Cache Efficiency</span>
                <span className="text-emerald-500 font-semibold">
                  {globalStats.cacheEfficiency}%
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">System Uptime</span>
                <span className="text-emerald-500 font-semibold">
                  {globalStats.uptime}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
