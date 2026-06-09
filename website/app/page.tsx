import Sidebar from "./Components/Sidebar";
import TopBar from "./Components/TopBar";
import RiskMap from "./Components/RiskMap";
import DriverMonitor from "./Components/DriverMonitor";
import AlertsPanel from "./Components/AlertsPanel";
import RouteRisk from "./Components/RouteRisk";
export default function Home() {
  return(
    <main className="flex-1 bg-[#0B0F19] text-white h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col p-4 gap-4">
        <TopBar />
        <div className="h-[50%] rounded-2x1 overflow-hidden border border-white/10">
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