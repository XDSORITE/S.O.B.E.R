import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import RiskMap from "./components/RiskMap";
import DriverMonitor from "./components/DriverMonitor";
import AlertsPanel from "./components/AlertsPanel";
import RouteRisk from "./components/RouteRisk";
export default function Home() {
  return(
    <main className="flex-1 bg-[#0B0F19] text-white h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col p-4 gap-4">
        <TopBar />
        <div className="h-[600] rounded-2x1 overflow-hidden border border-white/10">
        <RiskMap />
        </div>
        <div className="grid grid-cols-3 gap-4 h-[40%]">
          <DriverMonitor />
          <AlertsPanel />
          <RouteRisk />
        </div>
      </div>
    </main>
  );
}