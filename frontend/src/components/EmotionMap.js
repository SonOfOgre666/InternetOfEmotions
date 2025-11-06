import React, { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './EmotionMap.css';

const EMOTION_COLORS = {
  joy: '#4ade80',
  sadness: '#3b82f6',
  anger: '#ef4444',
  fear: '#a855f7',
  surprise: '#f59e0b',
  neutral: '#6b7280',
  disgust: '#ec4899'
};

const EMOTION_EMOJIS = {
  joy: '😊',
  sadness: '😢',
  anger: '😠',
  fear: '😰',
  surprise: '😲',
  neutral: '😐',
  disgust: '🤢'
};

// Component to handle country popup with aggregated data
const CountryPopup = ({ country, emotion }) => {
  const [countryData, setCountryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCountryData = async () => {
    if (countryData) return; // Already loaded
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:5000/api/country/${country}`);
      if (!response.ok) throw new Error('Failed to fetch country data');
      
      const data = await response.json();
      setCountryData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when popup opens
  React.useEffect(() => {
    fetchCountryData();
  }, [country]);

  if (loading) {
    return (
      <div className="country-popup loading">
        <p>Loading country data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="country-popup error">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!countryData) {
    return (
      <div className="country-popup">
        <p>No data available</p>
      </div>
    );
  }

  const { country_emotion, emotion_distribution, total_posts, top_events } = countryData;

  return (
    <div className="country-popup">
      <div className="country-header">
        <span className="country-emoji">
          {EMOTION_EMOJIS[country_emotion.dominant_emotion]}
        </span>
        <strong style={{ color: EMOTION_COLORS[country_emotion.dominant_emotion] }}>
          {country_emotion.dominant_emotion.toUpperCase()}
        </strong>
      </div>
      
      <div className="country-details">
        <h3>📍 {country}</h3>
        
        {/* NEW: Top Events/Topics Section */}
        {top_events && top_events.length > 0 && (
          <div className="top-events">
            <h4>🔥 Main Issues:</h4>
            <ul className="events-list">
              {top_events.map((event, idx) => (
                <li key={idx} className="event-item">
                  <strong>{event.topic}</strong> 
                  <span className="event-count">({event.count} posts)</span>
                  {event.top_post && (
                    <p className="event-preview">
                      {EMOTION_EMOJIS[event.top_post.emotion]} {event.top_post.text}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="country-stats">
          <p><strong>Confidence:</strong> {(country_emotion.confidence * 100).toFixed(0)}%</p>
          <p><strong>Analysis Method:</strong> {country_emotion.method}</p>
          <p><strong>Total Posts Analyzed:</strong> {total_posts}</p>
        </div>

        <div className="emotion-breakdown">
          <h4>Emotion Distribution:</h4>
          <div className="emotion-bars">
            {Object.entries(emotion_distribution).map(([emot, count]) => {
              const percentage = (count / total_posts) * 100;
              return (
                <div key={emot} className="emotion-bar-item">
                  <span className="emotion-bar-label">
                    {EMOTION_EMOJIS[emot]} {emot}
                  </span>
                  <div className="emotion-bar-container">
                    <div 
                      className="emotion-bar-fill"
                      style={{ 
                        width: `${percentage}%`,
                        backgroundColor: EMOTION_COLORS[emot]
                      }}
                    />
                  </div>
                  <span className="emotion-bar-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {country_emotion.algorithm_votes && (
          <div className="algorithm-consensus">
            <h4>Algorithm Consensus:</h4>
            <ul>
              {Object.entries(country_emotion.details.algorithm_consensus).map(([algo, result]) => (
                <li key={algo}><small>{result}</small></li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// Memoize the entire component to prevent re-renders when props don't change meaningfully
const EmotionMap = React.memo(({ emotions }) => {
  // Group emotions by country to show one marker per country
  const countryEmotions = React.useMemo(() => {
    const grouped = {};
    emotions.forEach(emotion => {
      if (!grouped[emotion.country]) {
        grouped[emotion.country] = emotion;
      }
    });
    return Object.values(grouped);
  }, [emotions]);

  return (
    <div className="emotion-map-container">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        minZoom={2}
        maxZoom={10}
        preferCanvas={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          updateWhenIdle={true}
          updateWhenZooming={false}
          keepBuffer={2}
        />

        {countryEmotions.map((emotion, index) => (
          <CircleMarker
            key={emotion.id || `${emotion.country}-${index}`}
            center={emotion.coords}
            radius={10}
            fillColor={EMOTION_COLORS[emotion.emotion] || EMOTION_COLORS.neutral}
            color="white"
            weight={2}
            opacity={0.9}
            fillOpacity={0.7}
          >
            <Popup 
              maxWidth={320}
              minWidth={250}
              autoPan={true}
              autoPanPadding={[100, 100]}
              autoPanPaddingTopLeft={[20, 20]}
              autoPanPaddingBottomRight={[20, 20]}
              keepInView={true}
              className="country-popup-container"
            >
              <CountryPopup country={emotion.country} emotion={emotion} />
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="map-legend">
        <h4>Emotion Key</h4>
        <div className="legend-items">
          {Object.entries(EMOTION_COLORS).map(([emotion, color]) => (
            <div key={emotion} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: color }}
              ></span>
              <span className="legend-emoji">{EMOTION_EMOJIS[emotion]}</span>
              <span className="legend-label">{emotion}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if emotions array length changed
  // or if the actual emotion IDs changed (not just the array reference)
  if (prevProps.emotions.length !== nextProps.emotions.length) {
    return false; // Re-render
  }
  
  // Check if emotion IDs are the same
  const prevIds = prevProps.emotions.map(e => e.id).join(',');
  const nextIds = nextProps.emotions.map(e => e.id).join(',');
  
  return prevIds === nextIds; // true = don't re-render, false = re-render
});

export default EmotionMap;
