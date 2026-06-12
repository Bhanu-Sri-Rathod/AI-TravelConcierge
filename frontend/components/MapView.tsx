'use client'
import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix default marker icon
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function MapUpdater({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView([lat, lon], 11, { animate: true })
  }, [lat, lon, map])
  return null
}

interface MapViewProps {
  lat: number
  lon: number
  name: string
}

export default function MapView({ lat, lon, name }: MapViewProps) {
  return (
    <div className="h-full w-full" style={{ minHeight: '300px' }}>
      <MapContainer
        center={[lat, lon]}
        zoom={11}
        style={{ height: '100%', width: '100%', background: '#1e293b' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[lat, lon]}>
          <Popup>
            <div style={{ color: '#1e293b', fontWeight: 600 }}>{name}</div>
            <div style={{ color: '#64748b', fontSize: '12px' }}>{lat.toFixed(4)}, {lon.toFixed(4)}</div>
          </Popup>
        </Marker>
        <MapUpdater lat={lat} lon={lon}/>
      </MapContainer>
    </div>
  )
}
