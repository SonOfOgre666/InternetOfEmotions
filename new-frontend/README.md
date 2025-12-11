# Internet of Emotions - Next.js Frontend

Modern Next.js frontend for the Internet of Emotions real-time global emotion tracker.

## Features

- 🗺️ **Interactive Emotion Map** - Visualize global emotions with Leaflet
- 🔴 **Real-time Updates** - SSE stream connection for live data
- 📊 **Analytics Dashboard** - Comprehensive statistics and insights
- 🎨 **Modern UI** - Built with Tailwind CSS and shadcn/ui
- ⚡ **Fast & Responsive** - Next.js 15 with App Router

## Prerequisites

- Node.js 18+ or Bun
- Backend running on `http://localhost:5000` (see `/backend` directory)

## Quick Start

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` if your backend runs on a different URL:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:5000
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```
   
   Open [http://localhost:3000](http://localhost:3000)

4. **Build for production**
   ```bash
   npm run build
   npm start
   ```

## Backend Connection

The frontend connects to the backend API with the following endpoints:

- `GET /api/emotions` - Fetch emotion data
- `GET /api/stats` - Get statistics
- `GET /api/health` - Check backend status
- `SSE /api/posts/stream` - Real-time post stream

### Connection Status

The app displays connection status:
- **● LIVE** - Connected to SSE stream
- **○ CONNECTING...** - Backend available, connecting
- **⚠ BACKEND OFFLINE** - Cannot reach backend
- **DEMO** - Backend running in demo mode

### Fallback Mode

If the backend is unavailable, you can toggle to mock data mode using the status bar button.

## Project Structure

```
src/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── EmotionMap.tsx    # Interactive map
│   ├── CountryCardList.tsx
│   ├── SearchBar.tsx
│   ├── AnalyticsPanel.tsx
│   └── DetailedAnalytics.tsx
└── lib/
    ├── data.ts           # Mock data & types
    ├── api.ts            # Backend API client
    ├── useBackend.ts     # Backend connection hook
    └── utils.ts          # Utilities
```

## Scripts

- `npm run dev` - Start development server (with Turbopack)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run linting and type checking
- `npm run format` - Format code with Biome

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:5000` |

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Maps**: Leaflet + react-leaflet
- **Icons**: Lucide React, country-flag-icons
- **Linting**: Biome, ESLint

## Backend Setup

Make sure the backend is running before starting the frontend:

```bash
cd ../backend
python app.py
```

See `/backend/README.md` for backend setup instructions.

## Troubleshooting

### Cannot connect to backend

1. Ensure backend is running: `cd ../backend && python app.py`
2. Check backend URL in `.env.local`
3. Verify CORS is enabled in backend
4. Check browser console for errors

### Map not loading

The map uses dynamic imports to avoid SSR issues. If you see errors:
1. Clear Next.js cache: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check browser console for Leaflet errors

### Build errors with TypeScript

Run type checking: `npm run lint`

Common fixes:
- Ensure all dependencies are installed
- Check `@types/geojson` is installed
- Clear build cache: `rm -rf .next`

## License

MIT
