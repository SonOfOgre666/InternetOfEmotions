'use client';

import { emotionConfig, type Emotion } from '@/lib/data';

interface SearchBarProps {
  searchQuery: string;
  selectedEmotion: Emotion | 'all';
  onSearchChange: (query: string) => void;
  onEmotionChange: (emotion: Emotion | 'all') => void;
}

export function SearchBar({
  searchQuery,
  selectedEmotion,
  onSearchChange,
  onEmotionChange,
}: SearchBarProps) {
  return (
    <div className="p-4 border-b border-zinc-800 space-y-3">
      {/* Search Input */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          placeholder="Search countries..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-600"
        />
      </div>

      {/* Emotion Filter Buttons */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-zinc-400 font-medium">Filter:</span>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => onEmotionChange('all')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              selectedEmotion === 'all'
                ? 'bg-zinc-700 text-zinc-100'
                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-750 hover:text-zinc-300'
            }`}
          >
            All
          </button>
          {Object.entries(emotionConfig).map(([key, config]) => (
            <button
              key={key}
              onClick={() => onEmotionChange(key as Emotion)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                selectedEmotion === key
                  ? 'bg-zinc-700 text-zinc-100'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-750 hover:text-zinc-300'
              }`}
            >
              {config.emoji} {config.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sort Options */}
      <div className="flex items-center gap-2 text-xs">
        <span className="text-zinc-400">Sort:</span>
        <select className="bg-zinc-800 border border-zinc-700 rounded-md px-2 py-1 text-zinc-300 text-xs focus:outline-none focus:ring-2 focus:ring-zinc-600">
          <option>Post Count (High to Low)</option>
          <option>Confidence (High to Low)</option>
          <option>Country Name (A-Z)</option>
          <option>Trending</option>
        </select>
      </div>
    </div>
  );
}
