export type Emotion = 'anger' | 'fear' | 'sadness' | 'joy' | 'neutral' | 'surprise' | 'disgust';

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

export const countriesData: CountryData[] = [
  {
    iso: 'USA',
    name: 'United States',
    emoji: '🇺🇸',
    capital: 'Washington, D.C.',
    emotion: 'anger',
    confidence: 78,
    postCount: 847,
    trend: 'up',
    distribution: { anger: 35, fear: 28, sadness: 17, neutral: 11, joy: 9, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Election results', count: 47 },
      { topic: 'Economic policies', count: 32 },
      { topic: 'Foreign relations', count: 28 },
    ],
    recentPosts: [
      'New policy announcement sparks heated debate among citizens',
      'Market reaction to latest news shows investor concerns',
      'Public opinion divided on recent government decisions',
    ],
  },
  {
    iso: 'GBR',
    name: 'United Kingdom',
    emoji: '🇬🇧',
    capital: 'London',
    emotion: 'fear',
    confidence: 72,
    postCount: 652,
    trend: 'steady',
    distribution: { fear: 38, anger: 24, sadness: 19, neutral: 12, joy: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Brexit implications', count: 41 },
      { topic: 'Healthcare system', count: 29 },
      { topic: 'Climate policies', count: 24 },
    ],
    recentPosts: [
      'Concerns grow over economic uncertainty in coming months',
      'Citizens express worry about future trade relationships',
      'Anxiety rises as new regulations take effect',
    ],
  },
  {
    iso: 'DEU',
    name: 'Germany',
    emoji: '🇩🇪',
    capital: 'Berlin',
    emotion: 'joy',
    confidence: 68,
    postCount: 521,
    trend: 'up',
    distribution: { joy: 42, neutral: 28, anger: 15, sadness: 10, fear: 5, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Green energy success', count: 38 },
      { topic: 'Economic growth', count: 31 },
      { topic: 'Cultural events', count: 22 },
    ],
    recentPosts: [
      'Celebration as renewable energy targets exceeded',
      'Positive outlook following strong economic indicators',
      'Community events bring people together nationwide',
    ],
  },
  {
    iso: 'FRA',
    name: 'France',
    emoji: '🇫🇷',
    capital: 'Paris',
    emotion: 'anger',
    confidence: 71,
    postCount: 489,
    trend: 'up',
    distribution: { anger: 39, fear: 22, sadness: 18, neutral: 14, joy: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Labor protests', count: 44 },
      { topic: 'Pension reforms', count: 36 },
      { topic: 'Immigration debate', count: 27 },
    ],
    recentPosts: [
      'Widespread protests continue over controversial reforms',
      'Public frustration mounts as negotiations stall',
      'Strikes disrupt major cities across the nation',
    ],
  },
  {
    iso: 'IND',
    name: 'India',
    emoji: '🇮🇳',
    capital: 'New Delhi',
    emotion: 'sadness',
    confidence: 65,
    postCount: 734,
    trend: 'steady',
    distribution: { sadness: 34, fear: 26, neutral: 20, anger: 13, joy: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Economic hardship', count: 52 },
      { topic: 'Environmental concerns', count: 38 },
      { topic: 'Social inequality', count: 31 },
    ],
    recentPosts: [
      'Communities struggle with ongoing economic challenges',
      'Concern over environmental degradation continues to grow',
      'Social issues dominate public discourse',
    ],
  },
  {
    iso: 'JPN',
    name: 'Japan',
    emoji: '🇯🇵',
    capital: 'Tokyo',
    emotion: 'neutral',
    confidence: 61,
    postCount: 412,
    trend: 'steady',
    distribution: { neutral: 48, sadness: 18, fear: 15, joy: 12, anger: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Aging population', count: 33 },
      { topic: 'Technology sector', count: 28 },
      { topic: 'Cultural preservation', count: 21 },
    ],
    recentPosts: [
      'Measured response to demographic challenges',
      'Technology advances continue at steady pace',
      'Balance sought between tradition and innovation',
    ],
  },
  {
    iso: 'BRA',
    name: 'Brazil',
    emoji: '🇧🇷',
    capital: 'Brasília',
    emotion: 'joy',
    confidence: 74,
    postCount: 598,
    trend: 'up',
    distribution: { joy: 45, neutral: 22, anger: 16, fear: 11, sadness: 6, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Carnival celebrations', count: 49 },
      { topic: 'Football victories', count: 42 },
      { topic: 'Cultural festivals', count: 34 },
    ],
    recentPosts: [
      'Nationwide celebrations as festival season begins',
      'Positive energy spreads across communities',
      'Cultural pride on full display in major cities',
    ],
  },
  {
    iso: 'CAN',
    name: 'Canada',
    emoji: '🇨🇦',
    capital: 'Ottawa',
    emotion: 'neutral',
    confidence: 59,
    postCount: 387,
    trend: 'steady',
    distribution: { neutral: 44, joy: 21, fear: 16, sadness: 12, anger: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Healthcare debate', count: 29 },
      { topic: 'Climate action', count: 26 },
      { topic: 'Indigenous rights', count: 22 },
    ],
    recentPosts: [
      'Calm discussions continue on policy matters',
      'Measured approach to addressing national issues',
      'Balanced perspectives emerge in public dialogue',
    ],
  },
  {
    iso: 'AUS',
    name: 'Australia',
    emoji: '🇦🇺',
    capital: 'Canberra',
    emotion: 'joy',
    confidence: 69,
    postCount: 445,
    trend: 'up',
    distribution: { joy: 41, neutral: 27, anger: 14, fear: 11, sadness: 7, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Sports achievements', count: 36 },
      { topic: 'Tourism boom', count: 31 },
      { topic: 'Economic recovery', count: 24 },
    ],
    recentPosts: [
      'Excitement builds around international sporting events',
      'Tourism sector shows strong recovery signs',
      'Optimism grows with positive economic indicators',
    ],
  },
  {
    iso: 'CHN',
    name: 'China',
    emoji: '🇨🇳',
    capital: 'Beijing',
    emotion: 'neutral',
    confidence: 63,
    postCount: 891,
    trend: 'steady',
    distribution: { neutral: 51, joy: 19, anger: 14, fear: 10, sadness: 6, surprise: 0, disgust: 0 },
    topTopics: [
      { topic: 'Economic development', count: 58 },
      { topic: 'Technology innovation', count: 47 },
      { topic: 'Infrastructure projects', count: 39 },
    ],
    recentPosts: [
      'Steady progress reported on major infrastructure initiatives',
      'Technology sector continues measured growth',
      'Economic indicators remain stable',
    ],
  },
];

export const globalStats = {
  postsPerMinute: 28,
  activeCountries: 145,
  cycleProgress: '3/196',
  cacheEfficiency: 95,
  uptime: 99.9,
  emotionTrends: {
    anger: { change: 15, direction: 'up' as const },
    fear: { change: 8, direction: 'up' as const },
    sadness: { change: 0, direction: 'steady' as const },
    joy: { change: 3, direction: 'down' as const },
    neutral: { change: 2, direction: 'up' as const },
    surprise: { change: 5, direction: 'up' as const },
    disgust: { change: 1, direction: 'steady' as const },
  },
};
