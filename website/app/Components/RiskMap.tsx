"use client";
import "leaflet/dist/leaflet.css";
import dynamic from "next/dynamic";
const Map = dynamic(
    async () => {
        const {
            MapContainer,
            TileLayer,
            Circle,
            Popup,
        } = await import("react-leaflet");
        return function DynamicMap() {
            const hotspots = [
                {
                    position: [34.0522, -118.2473],
                    risk: "High Risk - Los Angeles",
                    color: "red",
                },
                {
                    position: [40.7128, -74.006],
                    risk: "Moderate Risk - New York",
                    color: "yellow",
                },
                {
                    position: [41.8781, -87.6298],
                    risk: "Low Risk - Chicago",
                    color: "green",
                },
            ];
            return (
                <MapContainer center={[39.8283, -98.5795]} zoom={4} style={{width:"100%", height:"100%",}}>
                    <TileLayer attribution="OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    {hotspots.map((spot, index) => (
                        <Circle key={index} center={spot.position as [number, number]} radius={70000} pathOptions={{color:spot.color, fillColor: spot.color, fillOpacity: 0.4,}}>
                            <Popup>{spot.risk}</Popup>
                        </Circle>
                    ))}
                </MapContainer>
            );
        };
    },
    {
        ssr: false,
    }
);
export default function RiskMap() {
    return (
        <div className="h-full w-full">
            <Map />
        </div>
    );
}