'use client';

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet's default icon path issues in Next.js/Webpack
/* eslint-disable @typescript-eslint/no-explicit-any */
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapProps {
    data: any[];
    latCol: string;
    lonCol: string;
    numCol?: string; // Optional: use for radius size
}

// Component to adjust map bounds to fit markers
function MapBounds({ data, latCol, lonCol }: MapProps) {
    const map = useMap();

    useEffect(() => {
        if (data.length > 0) {
            const bounds = L.latLngBounds(data.map(d => [d[latCol], d[lonCol]]));
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [data, map, latCol, lonCol]);

    return null;
}

const MapComponent: React.FC<MapProps> = ({ data, latCol, lonCol, numCol }) => {
    // Filter valid coordinates
    const validData = data.filter(d =>
        d[latCol] != null && !isNaN(Number(d[latCol])) &&
        d[lonCol] != null && !isNaN(Number(d[lonCol]))
    );

    if (validData.length === 0) return <div>No valid geolocation data found.</div>;

    // Calculate center (fallback if fitBounds fails)
    const centerLat = validData.reduce((sum, d) => sum + Number(d[latCol]), 0) / validData.length;
    const centerLon = validData.reduce((sum, d) => sum + Number(d[lonCol]), 0) / validData.length;

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid #ddd', zIndex: 0 }}>
            <MapContainer
                center={[centerLat, centerLon]}
                zoom={5}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapBounds data={validData} latCol={latCol} lonCol={lonCol} />

                {validData.map((d, idx) => {
                    const lat = Number(d[latCol]);
                    const lon = Number(d[lonCol]);
                    const val = numCol ? d[numCol] : null;

                    // Dynamic styling based on value (if available) - Simple scaling
                    const radius = 6;

                    return (
                        <CircleMarker
                            key={idx}
                            center={[lat, lon]}
                            radius={radius}
                            pathOptions={{
                                color: '#ffffff',
                                fillColor: '#ff4d4f', // Red for emphasis
                                fillOpacity: 0.7,
                                weight: 1
                            }}
                        >
                            <Popup>
                                <div style={{ fontSize: '0.9rem' }}>
                                    <strong>Coordinates:</strong> {lat.toFixed(4)}, {lon.toFixed(4)}<br />
                                    {Object.entries(d).map(([k, v]) => {
                                        if (k === latCol || k === lonCol) return null;
                                        if (typeof v === 'object') return null;
                                        return <div key={k}><b>{k}:</b> {String(v)}</div>;
                                    })}
                                </div>
                            </Popup>
                        </CircleMarker>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
