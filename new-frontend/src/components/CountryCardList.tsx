'use client';

import { emotionConfig, type CountryData } from '@/lib/data';
import * as flags from 'country-flag-icons/react/3x2';

interface CountryCardListProps {
  countries: CountryData[];
  onCountrySelect: (country: CountryData) => void;
  selectedCountry: CountryData | null;
  hoveredCountry: string | null;
}

export function CountryCardList({
  countries,
  onCountrySelect,
  selectedCountry,
  hoveredCountry,
}: CountryCardListProps) {
  const getFlagComponent = (iso: string) => {
    // Map 3-letter codes to 2-letter codes
    const isoMap: Record<string, string> = {
      'USA': 'US',
      'GBR': 'GB',
      'DEU': 'DE',
      'FRA': 'FR',
      'IND': 'IN',
      'JPN': 'JP',
      'BRA': 'BR',
      'CAN': 'CA',
      'AUS': 'AU',
      'CHN': 'CN',
    };
    const code = isoMap[iso] || iso;
    const FlagComponent = (flags as Record<string, React.ComponentType<{ className?: string }>>)[code];
    return FlagComponent ? <FlagComponent className="w-8 h-6 rounded" /> : <span className="text-2xl">🏳️</span>;
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return '↗';
    if (trend === 'down') return '↘';
    return '→';
  };

  const getTrendColor = (trend: string) => {
    if (trend === 'up') return 'text-green-500';
    if (trend === 'down') return 'text-red-500';
    return 'text-zinc-400';
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-4 space-y-3">
        {countries.length === 0 ? (
          <div className="text-center py-8 text-zinc-500 text-sm">
            No countries match your filters
          </div>
        ) : (
          countries.map((country) => {
            const isSelected = selectedCountry?.iso === country.iso;
            const isHovered = hoveredCountry === country.iso;
            const emotionData = emotionConfig[country.emotion];

            return (
              <button
                key={country.iso}
                onClick={() => onCountrySelect(country)}
                className={`w-full text-left rounded-lg border transition-all ${
                  isSelected
                    ? 'bg-zinc-800 border-amber-500/50 shadow-lg shadow-amber-500/10'
                    : isHovered
                    ? 'bg-zinc-800/70 border-zinc-600'
                    : 'bg-zinc-850 border-zinc-800 hover:bg-zinc-800 hover:border-zinc-700'
                }`}
              >
                <div className="p-4">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getFlagComponent(country.iso)}
                      <div>
                        <h3 className="font-semibold text-zinc-100 text-sm">
                          {country.name}
                        </h3>
                        <p className="text-xs text-zinc-500">{country.iso}</p>
                      </div>
                    </div>
                    <div className={`text-lg ${getTrendColor(country.trend)}`}>
                      {getTrendIcon(country.trend)}
                    </div>
                  </div>

                  {/* Emotion */}
                  <div className="flex items-center gap-2 mb-3">
                    <div
                      className="w-full h-1.5 rounded-full bg-zinc-700 overflow-hidden"
                    >
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${country.confidence}%`,
                          backgroundColor: emotionData.color,
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="text-lg">{emotionData.emoji}</span>
                      <span className="text-sm font-medium text-zinc-300">
                        {emotionData.label}
                      </span>
                      <span className="text-xs text-zinc-500">
                        {country.confidence}%
                      </span>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="mt-3 flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1 text-zinc-400">
                      <svg
                        className="w-3.5 h-3.5"
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
                      <span>{country.postCount.toLocaleString()} posts</span>
                    </div>
                    <div className={`flex items-center gap-1 ${getTrendColor(country.trend)}`}>
                      <svg
                        className="w-3.5 h-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                        />
                      </svg>
                      <span className="capitalize">{country.trend}</span>
                    </div>
                  </div>

                  {/* Top Topic Preview */}
                  {country.topTopics[0] && (
                    <div className="mt-3 pt-3 border-t border-zinc-800">
                      <p className="text-xs text-zinc-500">
                        Top: <span className="text-zinc-400">{country.topTopics[0].topic}</span>
                      </p>
                    </div>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
