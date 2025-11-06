import React from 'react';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import './StatsPanel.css';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const EMOTION_COLORS = {
  joy: '#4ade80',
  sadness: '#3b82f6',
  anger: '#ef4444',
  fear: '#a855f7',
  surprise: '#f59e0b',
  neutral: '#6b7280'
};

function StatsPanel({ stats }) {
  if (!stats || stats.total === 0) {
    return (
      <div className="stats-panel">
        <h3>Statistics</h3>
        <p className="no-data">Waiting for data...</p>
      </div>
    );
  }

  const emotionData = {
    labels: Object.keys(stats.by_emotion).map(e => e.charAt(0).toUpperCase() + e.slice(1)),
    datasets: [
      {
        label: 'Emotions',
        data: Object.values(stats.by_emotion),
        backgroundColor: Object.keys(stats.by_emotion).map(e => EMOTION_COLORS[e] || '#6b7280'),
        borderColor: '#fff',
        borderWidth: 2,
      },
    ],
  };

  const countryData = {
    labels: Object.keys(stats.by_country).slice(0, 10),
    datasets: [
      {
        label: 'Posts by Country',
        data: Object.values(stats.by_country).slice(0, 10),
        backgroundColor: '#667eea',
        borderColor: '#667eea',
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 10,
          font: {
            size: 11
          }
        }
      },
    },
  };

  const barOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0
        }
      }
    }
  };

  return (
    <div className="stats-panel">
      <div className="stats-header">
        <h3>Statistics</h3>
        <span className="total-count">{stats.total} total</span>
      </div>

      <div className="chart-container">
        <h4>Emotion Distribution</h4>
        <div className="chart-wrapper" style={{ height: '200px' }}>
          <Doughnut data={emotionData} options={chartOptions} />
        </div>
      </div>

      <div className="chart-container">
        <h4>Top Countries</h4>
        <div className="chart-wrapper" style={{ height: '250px' }}>
          <Bar data={countryData} options={barOptions} />
        </div>
      </div>

      <div className="emotion-breakdown">
        <h4>Breakdown</h4>
        {Object.entries(stats.by_emotion)
          .sort((a, b) => b[1] - a[1])
          .map(([emotion, count]) => (
            <div key={emotion} className="emotion-row">
              <div className="emotion-info">
                <span
                  className="emotion-dot"
                  style={{ backgroundColor: EMOTION_COLORS[emotion] }}
                ></span>
                <span className="emotion-name">
                  {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                </span>
              </div>
              <div className="emotion-stats">
                <span className="emotion-count">{count}</span>
                <span className="emotion-percent">
                  {((count / stats.total) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

export default StatsPanel;
