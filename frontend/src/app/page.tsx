'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { CountryCardList } from '@/components/CountryCardList';
import { SearchBar } from '@/components/SearchBar';
import { AnalyticsPanel } from '@/components/AnalyticsPanel';
import { DetailedAnalytics } from '@/components/DetailedAnalytics';
import { type Emotion, type CountryData } from '@/lib/data';
import { useBackend } from '@/lib/useBackend';

// Dynamic import to avoid SSR issues with leaflet
const EmotionMap = dynamic(
  () => import('@/components/EmotionMap').then((mod) => mod.EmotionMap),
  { ssr: false, loading: () => <div className="w-full h-full bg-zinc-950 flex items-center justify-center"><div className="text-zinc-400 text-sm">Loading map...</div></div> }
);

export default function Home() {
  // Use backend hook for real data
  const {
    countries: backendCountries,
    isConnected,
    isBackendAvailable,
    demoMode,
    stats,
    recentPosts,
    error,
  } = useBackend();

  // Use backend data only - no mock data fallback
  const countries = backendCountries;

  const [selectedEmotion, setSelectedEmotion] = useState<Emotion | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState<CountryData | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  const filteredCountries = countries.filter((country) => {
    const matchesSearch = country.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesEmotion = selectedEmotion === 'all' || country.emotion === selectedEmotion;
    return matchesSearch && matchesEmotion;
  });

  // Update selected country when data changes
  useEffect(() => {
    if (selectedCountry) {
      const updated = countries.find((c) => c.iso === selectedCountry.iso);
      if (updated) {
        setSelectedCountry(updated);
      }
    }
  }, [countries, selectedCountry]);

  return (
    <div className="flex flex-col h-screen bg-zinc-950">
      {/* Main Content: Map + Sidebar + Analytics */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map Container */}
        <div className="flex-[8] relative flex flex-col">
          {/* Connection status indicator */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-lg px-3 py-1.5 shadow-xl flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 
              isBackendAvailable ? 'bg-yellow-500' : 
              'bg-red-500'
            }`} />
            <span className="text-xs text-zinc-300">
              {isConnected ? '● LIVE' : 
               isBackendAvailable ? '○ CONNECTING...' : 
               '⚠ BACKEND OFFLINE'}
            </span>
            {demoMode && <span className="ml-2 text-xs text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded">DEMO</span>}
            <span className="text-xs text-zinc-500 ml-2">
              {countries.length} countries • {stats?.total || 0} posts
            </span>
          </div>
          
          {/* Map */}
          <div className="flex-1">
            <EmotionMap
              countries={countries}
              selectedEmotion={selectedEmotion}
              onCountryClick={setSelectedCountry}
              onCountryHover={setHoveredCountry}
              selectedCountry={selectedCountry}
            />
          </div>
          
          {/* Analytics Panel at bottom of map area */}
          <div className="h-auto max-h-48 overflow-hidden">
            <AnalyticsPanel stats={stats} countries={countries} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="flex-[2] bg-zinc-900 border-l border-zinc-800 flex flex-col">
          {/* Search Bar */}
          <SearchBar
            searchQuery={searchQuery}
            selectedEmotion={selectedEmotion}
            onSearchChange={setSearchQuery}
            onEmotionChange={setSelectedEmotion}
          />

          {/* Country Cards List */}
          <CountryCardList
            countries={filteredCountries}
            onCountrySelect={setSelectedCountry}
            selectedCountry={selectedCountry}
            hoveredCountry={hoveredCountry}
          />
        </div>
      </div>

      {/* Detailed Country Analytics Modal/Panel */}
      {selectedCountry && (
        <DetailedAnalytics
          country={selectedCountry}
          onClose={() => setSelectedCountry(null)}
        />
      )}
    </div>
  );
}
