'use client';

import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { emotionConfig, type CountryData, type Emotion } from '@/lib/data';
import type * as GeoJSONTypes from 'geojson';

const WORLD_BOUNDS: L.LatLngBoundsExpression = [
  [-90, -180],
  [90, 180],
];

interface EmotionMapProps {
  countries: CountryData[];
  selectedEmotion: Emotion | 'all';
  onCountryClick: (country: CountryData | null) => void;
  onCountryHover: (iso: string | null) => void;
  selectedCountry: CountryData | null;
}

// Component to handle map updates
function MapController({
  selectedCountry,
  geoJsonData
}: {
  selectedCountry: CountryData | null;
  geoJsonData: GeoJSONTypes.FeatureCollection | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedCountry && geoJsonData) {
      // Find the feature for the selected country
      const feature = geoJsonData.features.find(
        (f: GeoJSONTypes.Feature) =>
          f.properties?.iso_a3 === selectedCountry.iso ||
          f.properties?.iso_a2 === selectedCountry.iso ||
          f.properties?.name === selectedCountry.name
      );

      if (feature) {
        const geoJsonLayer = L.geoJSON(feature);
        const bounds = geoJsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 5,
            animate: true,
            duration: 0.8
          });
        }
      }
    } else {
      // Reset to world view
      map.fitBounds(WORLD_BOUNDS, { animate: true, duration: 0.5 });
    }
  }, [selectedCountry, map, geoJsonData]);

  return null;
}

export function EmotionMap({
  countries,
  selectedEmotion,
  onCountryClick,
  onCountryHover,
  selectedCountry,
}: EmotionMapProps) {
  const [geoJsonData, setGeoJsonData] = useState<GeoJSONTypes.FeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const geoJsonRef = useRef<L.GeoJSON>(null);

  // Fetch GeoJSON data
  useEffect(() => {
    fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
      .then((response) => response.json())
      .then((data) => {
        setGeoJsonData(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error loading GeoJSON:', error);
        setLoading(false);
      });
  }, []);

  // Get country data by ISO code or name
  const getCountryData = (properties: GeoJSONTypes.GeoJsonProperties): CountryData | undefined => {
    return countries.find(
      (c) =>
        c.iso === properties?.iso_a3 ||
        c.iso === properties?.iso_a2 ||
        c.name.toLowerCase() === properties?.name?.toLowerCase()
    );
  };

  // Style function for GeoJSON features
  const styleFeature = (feature: GeoJSONTypes.Feature | undefined): L.PathOptions => {
    if (!feature) {
      return {
        fillColor: '#1a1a1a',
        fillOpacity: 0.7,
        color: '#27272a',
        weight: 0.5,
      };
    }
    
    const countryData = getCountryData(feature.properties);
    const isSelected = selectedCountry && countryData?.iso === selectedCountry.iso;

    if (!countryData) {
      // No data - neutral/default color
      return {
        fillColor: '#1a1a1a',
        fillOpacity: 0.7,
        color: '#27272a',
        weight: 0.5,
      };
    }

    // Filter by selected emotion
    if (selectedEmotion !== 'all' && countryData.emotion !== selectedEmotion) {
      return {
        fillColor: '#1a1a1a',
        fillOpacity: 0.3,
        color: '#27272a',
        weight: 0.5,
      };
    }

    const emotionColor = emotionConfig[countryData.emotion].color;
    const opacity = countryData.confidence / 100;

    return {
      fillColor: emotionColor,
      fillOpacity: opacity * 0.8,
      color: isSelected ? '#fbbf24' : '#27272a',
      weight: isSelected ? 3 : 0.8,
      dashArray: undefined,
    };
  };

  // Hover style
  const highlightFeature = (e: L.LeafletMouseEvent) => {
    const layer = e.target;
    const countryData = getCountryData(layer.feature.properties);

    if (countryData) {
      layer.setStyle({
        weight: 2.5,
        color: '#60a5fa',
        fillOpacity: 0.9,
      });
      layer.bringToFront();
      onCountryHover(countryData.iso);
    }
  };

  // Reset style
  const resetHighlight = (e: L.LeafletMouseEvent) => {
    if (geoJsonRef.current) {
      geoJsonRef.current.resetStyle(e.target);
    }
    onCountryHover(null);
  };

  // Click handler
  const onFeatureClick = (e: L.LeafletMouseEvent) => {
    const countryData = getCountryData(e.target.feature.properties);
    if (countryData) {
      onCountryClick(countryData);
    }
  };

  // Attach event handlers to each feature
  const onEachFeature = (feature: GeoJSONTypes.Feature, layer: L.Layer) => {
    layer.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
      click: onFeatureClick,
    });

    const countryData = getCountryData(feature.properties);
    if (countryData) {
      const emotionData = emotionConfig[countryData.emotion];
      layer.bindTooltip(
        `<div class="font-sans">
          <div class="font-semibold">${countryData.emoji} ${countryData.name}</div>
          <div class="text-xs mt-1">${emotionData.emoji} ${emotionData.label} (${countryData.confidence}%)</div>
          <div class="text-xs text-gray-400">${countryData.postCount.toLocaleString()} posts</div>
        </div>`,
        {
          direction: 'top',
          permanent: false,
          sticky: true,
          className: 'custom-tooltip',
        }
      );
    }
  };

  // Re-render GeoJSON when filters change
  useEffect(() => {
    if (geoJsonRef.current) {
      geoJsonRef.current.clearLayers();
      if (geoJsonData) {
        geoJsonRef.current.addData(geoJsonData);
      }
    }
  }, [selectedEmotion, selectedCountry, geoJsonData]);

  return (
    <div className="w-full h-full bg-zinc-950 relative">
      {/* Map Controls Overlay */}
      <div className="absolute top-4 left-4 z-[1000] bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-lg p-4 shadow-xl">
        <h3 className="text-sm font-semibold text-zinc-100 mb-3">Emotion Map Legend</h3>
        <div className="space-y-2 text-xs">
          {Object.entries(emotionConfig).map(([key, config]) => (
            <div key={key} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-zinc-300">{config.label}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-zinc-700 space-y-1">
          <p className="text-xs text-zinc-400">Click country to zoom & analyze</p>
          <p className="text-xs text-zinc-400">Hover for quick stats</p>
          <p className="text-xs text-zinc-400">Opacity = Confidence level</p>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-950 z-20">
          <div className="text-zinc-400 text-sm">Loading map data...</div>
        </div>
      )}

      {/* Map */}
      {!loading && geoJsonData && (
        <MapContainer
          center={[20, 0]}
          zoom={2}
          style={{ height: '100%', width: '100%', background: '#09090b' }}
          maxBounds={WORLD_BOUNDS}
          maxBoundsViscosity={1.0}
          minZoom={2}
          maxZoom={8}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          <GeoJSON
            ref={geoJsonRef}
            data={geoJsonData}
            style={styleFeature}
            onEachFeature={onEachFeature}
          />
          <MapController
            selectedCountry={selectedCountry}
            geoJsonData={geoJsonData}
          />
          <ZoomControl position="bottomright" />
        </MapContainer>
      )}

      {/* Filter indicator */}
      {selectedEmotion !== 'all' && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-zinc-900/95 backdrop-blur-sm border border-zinc-700 rounded-lg px-4 py-2 shadow-xl">
          <p className="text-xs text-zinc-400">
            Filtering:{' '}
            <span className="font-semibold text-zinc-100">
              {emotionConfig[selectedEmotion].emoji} {emotionConfig[selectedEmotion].label}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
