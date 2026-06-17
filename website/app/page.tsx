"use client";
import { useState } from "react";
import Sidebar from "./components/Sidebar";
import DashboardView from "./components/DashboardView";
import RiskMap from "./components/RiskMap";
import DriversView from "./components/RiskMap";
import AlertsView from "./components/AlertsView";
import AnalyticsView from "./components/AnalyticsView";
import SettingsView from "./components/SettingsView";

export default function Home() {
  const [active, setActive] = useState("Dashboard");
  const renderView = () => {
    switch (active) {
      case "Risk Map":
        return <RiskMap />;
      case "Drivers":
        return <DriversView />;
      case "Alerts":
        return <AlertsView />;
      case "Analytics":
        return <AnalyticsView />;
      case "Settings":
        return <SettingsView />;
      default:
        return <DashboardView />;
    }
  };
  return (
    <main className="flex h-screen bg-[#020617] text-white overflow-hidden">
      <Sidebar active={active} setActive={setActive} />
      <div className="flex-1 overflow-y-auto p-6">
        {renderView()}
      </div>
    </main>
  );
}