import React from 'react';
import './PostFeed.css';

const EMOTION_EMOJIS = {
  joy: '😊',
  sadness: '😢',
  anger: '😠',
  fear: '😰',
  surprise: '😲',
  neutral: '😐'
};

const EMOTION_COLORS = {
  joy: '#4ade80',
  sadness: '#3b82f6',
  anger: '#ef4444',
  fear: '#a855f7',
  surprise: '#f59e0b',
  neutral: '#6b7280'
};

function PostFeed({ posts }) {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="post-feed">
      <div className="feed-header">
        <h3>Live Feed</h3>
        <span className="feed-count">{posts.length} posts</span>
      </div>

      <div className="feed-content">
        {posts.length === 0 ? (
          <p className="no-posts">Waiting for posts...</p>
        ) : (
          posts.map((post, index) => (
            <div
              key={`${post.id}-${index}`}
              className="post-item"
              style={{ borderLeftColor: EMOTION_COLORS[post.emotion] }}
            >
              <div className="post-header">
                <span
                  className="post-emoji"
                  title={post.emotion}
                >
                  {EMOTION_EMOJIS[post.emotion]}
                </span>
                <span
                  className="post-emotion"
                  style={{ color: EMOTION_COLORS[post.emotion] }}
                >
                  {post.emotion.toUpperCase()}
                </span>
                <span className="post-confidence">
                  {(post.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <p className="post-text">{post.text}</p>

              <div className="post-meta">
                <span className="post-location">📍 {post.country}</span>
                <span className="post-source">
                  {post.url && post.url !== '#' ? (
                    <a href={post.url} target="_blank" rel="noopener noreferrer" className="post-link">
                      {post.source}
                    </a>
                  ) : (
                    post.source
                  )}
                </span>
                <span className="post-time">{formatTime(post.timestamp)}</span>
              </div>

              <div className="post-references">
                <span className="post-author">👤 {post.author}</span>
                <span className="post-score">⬆️ {post.score}</span>
                <span className="post-comments">💬 {post.num_comments}</span>
                {post.url && post.url !== '#' && (
                  <a href={post.url} target="_blank" rel="noopener noreferrer" className="post-external-link">
                    🔗 View on Reddit
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PostFeed;
