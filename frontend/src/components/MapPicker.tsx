import { useEffect, useState } from 'react'
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const icon = L.divIcon({
  className: '',
  html: '<div style="font-size:28px">📍</div>',
  iconSize: [28, 28],
  iconAnchor: [14, 28],
})

function ClickCapture({ onPick }: { onPick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) { onPick(e.latlng.lat, e.latlng.lng) },
  })
  return null
}

export default function MapPicker({ latitude, longitude, onChange }: {
  latitude: number | null
  longitude: number | null
  onChange: (lat: number, lon: number) => void
}) {
  const [pos, setPos] = useState<[number, number] | null>(
    latitude != null && longitude != null ? [latitude, longitude] : null,
  )

  useEffect(() => {
    setPos(latitude != null && longitude != null ? [latitude, longitude] : null)
  }, [latitude, longitude])

  return (
    <div className="space-y-2">
      <div className="h-56 overflow-hidden rounded-xl ring-1 ring-black/10">
        <MapContainer center={pos ?? [20.7, 77.0]} zoom={pos ? 12 : 5}
                      style={{ height: '100%', width: '100%' }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                     attribution="© OpenStreetMap" />
          <ClickCapture onPick={(lat, lon) => { setPos([lat, lon]); onChange(lat, lon) }} />
          {pos && <Marker position={pos} icon={icon} draggable
                          eventHandlers={{ dragend: (e) => {
                            const { lat, lng } = (e.target as L.Marker).getLatLng()
                            setPos([lat, lng]); onChange(lat, lng)
                          } }} />}
        </MapContainer>
      </div>
      <p className="text-xs text-gray-500">
        {pos ? `${pos[0].toFixed(4)}, ${pos[1].toFixed(4)} — tap or drag the pin` : 'Tap the map to place the pin'}
      </p>
    </div>
  )
}
