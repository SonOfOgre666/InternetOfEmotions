import React, { useState, useEffect } from 'react';
import EmotionMap from './components/EmotionMap';
import StatsPanel from './components/StatsPanel';
import PostFeed from './components/PostFeed';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [emotions, setEmotions] = useState([]);
  const [stats, setStats] = useState(null);
  const [posts, setPosts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [backendAvailable, setBackendAvailable] = useState(true);

  // Fetch initial data
  useEffect(() => {
    fetchEmotions();
    fetchStats();

    // Refresh data every 30 seconds to keep map updated
    // Only if backend is available
    const interval = setInterval(() => {
      if (backendAvailable) {
        fetchEmotions();
        fetchStats();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [backendAvailable]);

  // Connect to SSE stream
  useEffect(() => {
    if (!backendAvailable) return;

    let eventSource;
    let retryTimeout;

    const connectStream = () => {
      try {
        eventSource = new EventSource(`${API_BASE}/api/posts/stream`);

        eventSource.onopen = () => {
          console.log('✓ Connected to emotion stream');
          setIsConnected(true);
          setBackendAvailable(true);
        };

        eventSource.onmessage = (event) => {
          const newPost = JSON.parse(event.data);

          // Add to emotions WITHOUT trimming (let the 60s refresh handle full updates)
          // This prevents dots from disappearing as new posts come in
          setEmotions(prev => {
            // Check if post already exists (avoid duplicates)
            const exists = prev.some(p => p.id === newPost.id);
            if (exists) return prev;
            return [...prev, newPost];
          });

          // Add to posts feed (keep last 20)
          setPosts(prev => [newPost, ...prev.slice(0, 19)]);

          // Only refresh stats occasionally (every 10 posts)
          if (Math.random() < 0.1) {
            fetchStats();
          }
        };

        eventSource.onerror = (error) => {
          console.error('Stream error - retrying in 10 seconds...');
          setIsConnected(false);
          setBackendAvailable(false);
          eventSource.close();

          // Retry connection after 10 seconds (don't reload page)
          retryTimeout = setTimeout(() => {
            setBackendAvailable(true);
          }, 10000);
        };
      } catch (error) {
        console.error('Failed to connect to stream:', error);
        setBackendAvailable(false);
        retryTimeout = setTimeout(() => {
          setBackendAvailable(true);
        }, 10000);
      }
    };

    connectStream();

    return () => {
      if (eventSource) eventSource.close();
      if (retryTimeout) clearTimeout(retryTimeout);
    };
  }, [backendAvailable]);

  const fetchEmotions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/emotions`);
      if (!response.ok) {
        setBackendAvailable(false);
        return;
      }
      const data = await response.json();
      setEmotions(data.emotions || []);
      setDemoMode(data.demo_mode || false);
      setBackendAvailable(true);
    } catch (error) {
      console.error('Backend not available');
      setBackendAvailable(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/stats`);
      if (!response.ok) return;
      const data = await response.json();
      setStats(data);
    } catch (error) {
      // Silently fail for stats
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌍 Internet of Emotions</h1>
        <p>Real-time Global Emotion Tracker</p>
        <div className="status-bar">
          <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● LIVE' : backendAvailable ? '○ CONNECTING...' : '⚠ BACKEND OFFLINE'}
          </span>
          {demoMode && <span className="demo-badge">DEMO MODE</span>}
          <span className="count">
            {emotions.length} emotions tracked
          </span>
        </div>
      </header>

      <div className="dashboard">
        <div className="main-content">
          <EmotionMap emotions={emotions} />
        </div>

        <div className="sidebar">
          <StatsPanel stats={stats} />
          <PostFeed posts={posts} />
        </div>
      </div>

      <footer className="App-footer">
        <p>
          Powered by Reddit API • AI/ML Models: RoBERTa + BART + NER + CLIP + BLIP
        </p>
        {demoMode && (
          <p className="demo-notice">
            Running in demo mode. Configure Reddit API in .env for live data.
          </p>
        )}
      </footer>
    </div>
  );
}

export default App;
