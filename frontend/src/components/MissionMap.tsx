"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const markerIcon = L.icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

type MissionMapProps = {
  latitude?: number;
  longitude?: number;
  detectionName?: string;
  confidence?: number;
  priority?: string;
};

export default function MissionMap({
  latitude = 13.3409,
  longitude = 77.101,
  detectionName = "Detected Anomaly",
  confidence = 0,
  priority = "MEDIUM",
}: MissionMapProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-700">
      <MapContainer
        center={[latitude, longitude]}
        zoom={12}
        scrollWheelZoom={true}
        className="h-[420px] w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Marker
          position={[latitude, longitude]}
          icon={markerIcon}
        >
          <Popup>
            <div className="text-sm">
              <strong>{detectionName}</strong>

              <br />

              Confidence:{" "}
              {(confidence * 100).toFixed(1)}%

              <br />

              Priority: {priority}

              <br />

              <span className="text-xs">
                Simulated mission location
              </span>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}